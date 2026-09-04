import cv2
import json
import http.server
import pathlib
import subprocess
import sys
import threading
import webbrowser


RESULT_FILE = pathlib.Path(__file__).resolve().parent / "dunk_result.json"

from analysis.stability import calculate_stability
from analysis.breakage import predict_breakage
from analysis.dunk_score import calculate_dunk_score, get_dunk_rating
from analysis.movement import MovementTracker
from analysis.stability_graph import draw_stability_graph

from analysis.angle import (
    BiscuitAngleDetector,
    orientation_line_points
)

from analysis.dunk_result import (
    DunkResult,
    show_final_dunk_screen
)

from analysis.dunk_timer import DunkTimer

from analysis.immersion import (
    ImmersionRecorder,
    calculate_immersion
)


# -----------------------------------
# VARIABLES
# -----------------------------------

tracking = False
tracker = None

beverage_surface = None

selecting = False
start_x = 0
start_y = 0
selection_box = None

current_frame = None


# -----------------------------------
# ANALYSIS OBJECTS
# -----------------------------------

dunk_timer = DunkTimer()
angle_detector = BiscuitAngleDetector()
immersion_recorder = ImmersionRecorder()
dunk_result = DunkResult()

movement_tracker = MovementTracker()

stability_history = []
stability_times = []

current_stability = 100.0
current_breakage = 0.0
current_score = 0.0

dunk_was_running = False


# -----------------------------------
# HOME SCREEN
# -----------------------------------

def show_how_it_works(parent):

    popup = tk.Toplevel(parent)
    popup.title("How It Works")
    popup.configure(bg="#fffaf0")
    popup.resizable(False, False)
    popup.transient(parent)
    popup.grab_set()

    content = tk.Frame(
        popup,
        bg="#fffaf0",
        padx=32,
        pady=26
    )
    content.pack()

    tk.Label(
        content,
        text="HOW IT WORKS",
        bg="#fffaf0",
        fg="#29251f",
        font=("Comic Sans MS", 18, "bold")
    ).pack(pady=(0, 14))

    tk.Label(
        content,
        text=(
            "1. Select your biscuit\n"
            "2. Calibrate the beverage surface\n"
            "3. Dunk the biscuit\n"
            "4. AI analyzes immersion, angle and movement\n"
            "5. Get stability, breakage risk and dunk score"
        ),
        justify="left",
        bg="#fffaf0",
        fg="#51483d",
        font=("Comic Sans MS", 11),
        padx=8,
        pady=4
    ).pack()

    tk.Button(
        content,
        text="CLOSE",
        command=popup.destroy,
        bg="#e7a64a",
        fg="#29251f",
        activebackground="#d58d2f",
        relief="flat",
        cursor="hand2",
        font=("Comic Sans MS", 10, "bold"),
        padx=18,
        pady=7
    ).pack(pady=(18, 0))


def show_home_screen():

    camera_requested = False
    root = tk.Tk()
    root.title("Biscuit Dunk AI")
    root.configure(bg="#f5eddf")
    root.minsize(620, 500)

    def open_camera():
        nonlocal camera_requested
        camera_requested = True
        root.destroy()

    paper = tk.Frame(
        root,
        bg="#fffaf0",
        padx=60,
        pady=48,
        highlightbackground="#29251f",
        highlightthickness=2
    )
    paper.pack(expand=True, padx=36, pady=36)

    tk.Label(
        paper,
        text="Biscuit Dunk AI",
        bg="#fffaf0",
        fg="#e27d4f",
        font=("Comic Sans MS", 14, "bold")
    ).pack(pady=(0, 34))

    tk.Label(
        paper,
        text="Hello Chayae, kadi undo???",
        bg="#fffaf0",
        fg="#29251f",
        font=("Comic Sans MS", 27, "bold"),
        wraplength=560
    ).pack()

    tk.Label(
        paper,
        text="AI-Powered Biscuit Dunk Analysis",
        bg="#fffaf0",
        fg="#6b5d4d",
        font=("Comic Sans MS", 12)
    ).pack(pady=(14, 34))

    tk.Button(
        paper,
        text="OPEN CAMERA",
        command=open_camera,
        bg="#e7a64a",
        fg="#29251f",
        activebackground="#d58d2f",
        relief="flat",
        cursor="hand2",
        font=("Comic Sans MS", 15, "bold"),
        padx=34,
        pady=13
    ).pack()

    tk.Button(
        paper,
        text="HOW IT WORKS",
        command=lambda: show_how_it_works(root),
        bg="#c9d8bd",
        fg="#29251f",
        activebackground="#afc39e",
        relief="flat",
        cursor="hand2",
        font=("Comic Sans MS", 10, "bold"),
        padx=20,
        pady=8
    ).pack(pady=(18, 0))

    tk.Label(
        paper,
        text="Biscuit Dunk AI",
        bg="#fffaf0",
        fg="#8b7a68",
        font=("Comic Sans MS", 9)
    ).pack(pady=(40, 0))

    root.mainloop()
    return camera_requested


class HomePageHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/open-camera":

            subprocess.Popen(
                [sys.executable, str(pathlib.Path(__file__).resolve()), "--camera"]
            )

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Camera starting")
            return

        if self.path == "/result":

            if not RESULT_FILE.exists():
                self.send_response(202)
                self.end_headers()
                return

            result_data = RESULT_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(result_data)))
            self.end_headers()
            self.wfile.write(result_data)
            return

        super().do_GET()

    def log_message(self, format, *args):
        return


def show_html_home():

    if RESULT_FILE.exists():
        RESULT_FILE.unlink()

    project_folder = pathlib.Path(__file__).resolve().parent
    handler = lambda *args, **kwargs: HomePageHandler(
        *args,
        directory=str(project_folder),
        **kwargs
    )

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler
    )
    port = server.server_address[1]
    webbrowser.open(f"http://127.0.0.1:{port}/index.html")
    server.serve_forever()
    server.server_close()


def save_result_for_website():

    result_data = {
        "completed": dunk_result.dunk_completed,
        "immersion": dunk_result.final_immersion,
        "dunk_time": dunk_result.final_dunk_time,
        "angle": dunk_result.final_angle,
        "stability": dunk_result.final_stability,
        "breakage": dunk_result.final_breakage,
        "score": dunk_result.final_score,
        "rating": dunk_result.final_rating,
        "stability_times": stability_times,
        "stability_values": stability_history
    }

    RESULT_FILE.write_text(
        json.dumps(result_data, ensure_ascii=False),
        encoding="utf-8"
    )


# -----------------------------------
# MOUSE FUNCTION
# -----------------------------------

def select_biscuit(event, x, y, flags, param):

    global tracking
    global tracker

    global selecting
    global start_x
    global start_y
    global selection_box

    global current_frame

    if current_frame is None:
        return

    if event == cv2.EVENT_LBUTTONDOWN:

        selecting = True

        start_x = x
        start_y = y

        selection_box = None


    elif event == cv2.EVENT_MOUSEMOVE:

        if selecting:

            x1 = min(start_x, x)
            y1 = min(start_y, y)

            x2 = max(start_x, x)
            y2 = max(start_y, y)

            selection_box = (
                x1,
                y1,
                x2 - x1,
                y2 - y1
            )


    elif event == cv2.EVENT_LBUTTONUP:

        selecting = False

        x1 = min(start_x, x)
        y1 = min(start_y, y)

        x2 = max(start_x, x)
        y2 = max(start_y, y)

        w = x2 - x1
        h = y2 - y1

        if w > 20 and h > 20:

            tracker = cv2.legacy.TrackerCSRT_create()

            tracker.init(
                current_frame,
                (x1, y1, w, h)
            )

            tracking = True

            selection_box = None

            print("Biscuit selected!")


# -----------------------------------
# CAMERA
# -----------------------------------

if "--camera" not in sys.argv:
    show_html_home()
    raise SystemExit


cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("Could not open camera")
    exit()


cv2.namedWindow(
    "Biscuit Dunk AI"
)

cv2.setMouseCallback(
    "Biscuit Dunk AI",
    select_biscuit
)


# -----------------------------------
# MAIN LOOP
# -----------------------------------

while True:

    ret, frame = cap.read()

    if not ret:

        print("Camera error")
        break


    frame = cv2.flip(
        frame,
        1
    )


    # Save clean frame
    current_frame = frame.copy()


    # -----------------------------------
    # SELECTION BOX
    # -----------------------------------

    if selecting and selection_box:

        x, y, w, h = selection_box

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 255),
            2
        )


    # -----------------------------------
    # TRACK BISCUIT
    # -----------------------------------

    biscuit = None

    if tracking:

        success, box = tracker.update(frame)


        if success:

            x, y, w, h = [
                int(v)
                for v in box
            ]

            center_x = x + w // 2
            center_y = y + h // 2

            biscuit_bottom = y + h


            biscuit = {
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "center_x": center_x,
                "center_y": center_y,
                "bottom": biscuit_bottom
            }


            # -----------------------------------
            # BISCUIT BOX
            # -----------------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                3
            )


            cv2.circle(
                frame,
                (
                    center_x,
                    center_y
                ),
                5,
                (0, 0, 255),
                -1
            )


            cv2.putText(
                frame,
                "BISCUIT",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


        else:

            tracking = False
            tracker = None

            cv2.putText(
                frame,
                "TRACKING LOST",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )


    # -----------------------------------
    # BEVERAGE SURFACE
    # -----------------------------------

    if beverage_surface is None:

        cv2.putText(
            frame,
            "Press C to set beverage surface",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

    else:

        cv2.line(
            frame,
            (0, beverage_surface),
            (
                frame.shape[1],
                beverage_surface
            ),
            (255, 0, 0),
            3
        )

        cv2.putText(
            frame,
            "BEVERAGE SURFACE",
            (
                20,
                beverage_surface - 10
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2
        )


    # -----------------------------------
    # IMMERSION + DUNK STATE
    # -----------------------------------

    current_immersion = 0.0

    if biscuit and beverage_surface is not None:

        current_immersion = calculate_immersion(
            biscuit["bottom"],
            biscuit["h"],
            beverage_surface
        )

        immersed = current_immersion > 0

        dunk_timer.update(immersed)

        dunk_is_running = dunk_timer.is_running()


        # -----------------------------------
        # DUNK START
        # -----------------------------------

        if dunk_is_running and not dunk_was_running:

            immersion_recorder.start_dunk()

            angle_detector.start_measuring()

            dunk_result.reset()

            movement_tracker.reset()

            stability_history.clear()
            stability_times.clear()

            current_stability = 100.0
            current_breakage = 0.0
            current_score = 0.0


        # -----------------------------------
        # DURING DUNK
        # -----------------------------------

        if dunk_is_running:

            immersion_recorder.update(
                current_immersion
            )


            # Angle
            angle_detector.calculate_biscuit_angle(
                current_frame,
                (
                    biscuit["x"],
                    biscuit["y"],
                    biscuit["w"],
                    biscuit["h"]
                )
            )


            # Movement
            movement = movement_tracker.update(
                biscuit["center_x"],
                biscuit["center_y"]
            )


            # Current angle
            current_angle = angle_detector.get_angle()

            if current_angle is None:
                current_angle = 0.0


            # -----------------------------------
            # STABILITY
            # -----------------------------------

            current_stability = calculate_stability(
                current_immersion,
                dunk_timer.get_elapsed_time(),
                current_angle,
                movement
            )


            # -----------------------------------
            # BREAKAGE
            # -----------------------------------

            current_breakage = predict_breakage(
                current_immersion,
                dunk_timer.get_elapsed_time(),
                current_angle,
                movement,
                current_stability
            )


            # -----------------------------------
            # DUNK SCORE
            # -----------------------------------

            current_score = calculate_dunk_score(
                dunk_timer.get_elapsed_time(),
                current_immersion,
                current_angle,
                movement,
                current_stability
            )


            # -----------------------------------
            # STABILITY HISTORY
            # -----------------------------------

            stability_history.append(
                current_stability
            )

            stability_times.append(
                dunk_timer.get_elapsed_time()
            )


        # -----------------------------------
        # DUNK END
        # -----------------------------------

        if dunk_was_running and not dunk_is_running:

            immersion_recorder.stop_dunk()

            angle_detector.stop_measuring()


            final_immersion = (
                immersion_recorder.get_max_immersion()
            )

            final_time = (
                dunk_timer.get_elapsed_time()
            )

            final_angle = (
                angle_detector.get_angle()
            )


            if final_angle is None:
                final_angle = 0.0


            # Use the last measured movement
            final_movement = (
                movement_tracker.get_movement()
                if hasattr(
                    movement_tracker,
                    "get_movement"
                )
                else 0.0
            )


            # -----------------------------------
            # FINAL STABILITY
            # -----------------------------------

            final_stability = calculate_stability(
                final_immersion,
                final_time,
                final_angle,
                final_movement
            )


            # -----------------------------------
            # FINAL BREAKAGE
            # -----------------------------------

            final_breakage = predict_breakage(
                final_immersion,
                final_time,
                final_angle,
                final_movement,
                final_stability
            )


            # -----------------------------------
            # FINAL SCORE
            # -----------------------------------

            final_score = calculate_dunk_score(
                final_time,
                final_immersion,
                final_angle,
                final_movement,
                final_stability
            )


            # -----------------------------------
            # FINAL RATING
            # -----------------------------------

            final_rating = get_dunk_rating(
                final_score
            )


            # -----------------------------------
            # ADD FINAL POINT TO GRAPH
            # -----------------------------------

            stability_history.append(
                final_stability
            )

            stability_times.append(
                final_time
            )


            # -----------------------------------
            # STORE COMPLETE RESULT
            # -----------------------------------

            dunk_result.store(
                final_immersion,
                final_time,
                final_angle,
                final_stability,
                final_breakage,
                final_score,
                final_rating
            )


            # Keep latest values
            current_stability = final_stability
            current_breakage = final_breakage
            current_score = final_score


            # -----------------------------------
            # PRINT FINAL RESULT
            # -----------------------------------

            print()
            print("========== DUNK RESULT ==========")

            print(
                f"Immersion      : "
                f"{final_immersion:.1f}%"
            )

            print(
                f"Dunk Time      : "
                f"{final_time:.2f} s"
            )

            print(
                f"Angle          : "
                f"{final_angle:.1f} deg"
            )

            print(
                f"Stability      : "
                f"{final_stability:.1f}"
            )

            print(
                f"Break Risk     : "
                f"{final_breakage:.1f}%"
            )

            print(
                f"Dunk Score     : "
                f"{final_score:.1f}/100"
            )

            print(
                f"Rating         : "
                f"{final_rating}"
            )

            print("=================================")


        dunk_was_running = dunk_is_running


        # -----------------------------------
        # DUNK STATUS
        # -----------------------------------

        if current_immersion <= 0:

            status = "ABOVE BEVERAGE"

        elif current_immersion < 100:

            status = "PARTIALLY IMMERSED"

        else:

            status = "FULLY IMMERSED"


        cv2.putText(
            frame,
            status,
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )


    # -----------------------------------
    # ANGLE + ORIENTATION LINE
    # -----------------------------------

    biscuit_angle = angle_detector.get_angle()

    show_angle = (
        biscuit_angle is not None
        and (
            dunk_timer.is_running()
            or dunk_result.dunk_completed
        )
    )


    if biscuit and show_angle:

        line_start, line_end = (
            orientation_line_points(
                biscuit["center_x"],
                biscuit["center_y"],
                biscuit_angle,
                biscuit["w"],
                biscuit["h"]
            )
        )


        cv2.line(
            frame,
            line_start,
            line_end,
            (255, 0, 255),
            3
        )


    # -----------------------------------
    # IMMERSION DISPLAY
    # -----------------------------------

    if dunk_timer.is_running():

        immersion_text = (
            f"IMMERSION: "
            f"{current_immersion:.1f}%"
        )

    elif dunk_result.dunk_completed:

        immersion_text = (
            f"MAX IMMERSION: "
            f"{dunk_result.final_immersion:.1f}%"
        )

    else:

        immersion_text = "IMMERSION: 0.0%"


    cv2.putText(
        frame,
        immersion_text,
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 0),
        2
    )


    # -----------------------------------
    # DUNK TIMER
    # -----------------------------------

    dunk_elapsed = (
        dunk_timer.get_elapsed_time()
    )

    dunk_status = (
        dunk_timer.get_ui_status()
    )


    if dunk_status == "COMPLETED":

        dunk_time_text = (
            f"DUNK COMPLETE: "
            f"{dunk_elapsed:.2f} s"
        )

    else:

        dunk_time_text = (
            f"DUNK TIME: "
            f"{dunk_elapsed:.2f} s"
        )


    cv2.putText(
        frame,
        dunk_time_text,
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"STATUS: {dunk_status}",
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # -----------------------------------
    # ANGLE DISPLAY
    # -----------------------------------

    if show_angle:

        cv2.putText(
            frame,
            f"ANGLE: {biscuit_angle:.1f} deg",
            (20, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 255),
            2
        )


    # -----------------------------------
    # STABILITY / BREAKAGE / SCORE
    # -----------------------------------

    if dunk_timer.is_running():

        cv2.putText(
            frame,
            f"STABILITY: {current_stability:.1f}",
            (20, 280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            f"BREAK RISK: {current_breakage:.1f}%",
            (20, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )


        cv2.putText(
            frame,
            f"DUNK SCORE: {current_score:.1f}/100",
            (20, 360),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )


    # -----------------------------------
    # IMPORTANT:
    # NO STABILITY GRAPH HERE
    # -----------------------------------
    #
    # The graph is intentionally NOT drawn
    # during the webcam loop.
    #
    # It will appear only on the final
    # result screen after the dunk.


    # -----------------------------------
    # INSTRUCTIONS
    # -----------------------------------

    if not tracking:

        cv2.putText(
            frame,
            "CLICK AND DRAG AROUND BISCUIT",
            (20, frame.shape[0] - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

    else:

        cv2.putText(
            frame,
            "R = reset biscuit",
            (20, frame.shape[0] - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


    cv2.putText(
        frame,
        "C = beverage | R = reset | ESC = exit",
        (20, frame.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )


    # -----------------------------------
    # DISPLAY
    # -----------------------------------

    cv2.imshow(
        "Biscuit Dunk AI",
        frame
    )


    key = cv2.waitKey(1) & 0xFF


    # -----------------------------------
    # CALIBRATE BEVERAGE
    # -----------------------------------

    if key == ord("c"):

        beverage_surface = (
            frame.shape[0] // 2
        )

        print(
            "Beverage surface calibrated at:",
            beverage_surface
        )


    # -----------------------------------
    # RESET
    # -----------------------------------

    if key == ord("r"):

        tracking = False
        tracker = None

        dunk_timer.reset()
        angle_detector.reset()
        immersion_recorder.reset()
        dunk_result.reset()

        movement_tracker.reset()

        stability_history.clear()
        stability_times.clear()

        current_stability = 100.0
        current_breakage = 0.0
        current_score = 0.0

        dunk_was_running = False

        print(
            "Biscuit tracking reset"
        )


    # -----------------------------------
    # EXIT
    # -----------------------------------

    if key == 27:

        break


# -----------------------------------
# CLEANUP
# -----------------------------------

cap.release()

cv2.destroyWindow(
    "Biscuit Dunk AI"
)


# -----------------------------------
# FINAL RESULT SCREEN
# -----------------------------------

show_final_dunk_screen(
    dunk_result,
    stability_times,
    stability_history
)

save_result_for_website()


cv2.destroyAllWindows()