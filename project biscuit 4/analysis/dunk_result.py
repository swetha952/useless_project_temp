"""
Final result of one completed dunk.

Stores:

    final_immersion
    final_dunk_time
    final_angle
    final_stability
    final_breakage
    final_score
    final_rating
    dunk_completed
"""

import cv2
import numpy as np

from analysis.stability_graph import draw_stability_graph


class DunkResult:
    """Container for the last completed dunk."""

    def __init__(self):
        self.reset()


    def reset(self):
        """Clear stored dunk data."""

        self.final_immersion = 0.0
        self.final_dunk_time = 0.0
        self.final_angle = None

        self.final_stability = 100.0
        self.final_breakage = 0.0
        self.final_score = 0.0
        self.final_rating = ""

        self.dunk_completed = False


    def store(
        self,
        immersion,
        dunk_time,
        angle,
        stability=100.0,
        breakage=0.0,
        score=0.0,
        rating=""
    ):
        """Freeze the complete result when the dunk ends."""

        self.final_immersion = immersion
        self.final_dunk_time = dunk_time
        self.final_angle = angle

        self.final_stability = stability
        self.final_breakage = breakage
        self.final_score = score
        self.final_rating = rating

        self.dunk_completed = True


def _put(
    image,
    text,
    x,
    y,
    scale,
    colour,
    thickness=2
):
    """Draw one line of text."""

    cv2.putText(
        image,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        colour,
        thickness,
        cv2.LINE_AA
    )


def show_final_dunk_screen(
    dunk_result,
    stability_times,
    stability_values
):
    """
    Show the final result screen.

    Results appear first.
    Stability graph appears below the results.
    """

    width = 900
    height = 780

    image = np.zeros(
        (height, width, 3),
        dtype=np.uint8
    )

    image[:] = (28, 24, 20)


    # -----------------------------------
    # OUTER BORDER
    # -----------------------------------

    cv2.rectangle(
        image,
        (30, 30),
        (width - 30, height - 30),
        (70, 60, 50),
        2
    )


    if dunk_result.dunk_completed:

        # -----------------------------------
        # TITLE
        # -----------------------------------

        _put(
            image,
            "DUNK COMPLETE",
            300,
            80,
            1.3,
            (0, 255, 255),
            3
        )


        # -----------------------------------
        # RESULTS
        # -----------------------------------

        _put(
            image,
            f"Immersion : "
            f"{dunk_result.final_immersion:.1f}%",
            100,
            140,
            0.8,
            (0, 255, 0),
            2
        )


        _put(
            image,
            f"Dunk Time : "
            f"{dunk_result.final_dunk_time:.2f} s",
            100,
            180,
            0.8,
            (0, 255, 255),
            2
        )


        if dunk_result.final_angle is None:

            angle_text = "Angle     : n/a"

        else:

            angle_text = (
                f"Angle     : "
                f"{dunk_result.final_angle:.1f} deg"
            )


        _put(
            image,
            angle_text,
            100,
            220,
            0.8,
            (255, 0, 255),
            2
        )


        _put(
            image,
            f"Stability : "
            f"{dunk_result.final_stability:.1f}",
            100,
            260,
            0.8,
            (0, 255, 0),
            2
        )


        _put(
            image,
            f"Break Risk: "
            f"{dunk_result.final_breakage:.1f}%",
            100,
            300,
            0.8,
            (0, 0, 255),
            2
        )


        _put(
            image,
            f"Dunk Score: "
            f"{dunk_result.final_score:.1f}/100",
            100,
            340,
            0.8,
            (255, 255, 0),
            2
        )


        _put(
            image,
            f"Rating    : "
            f"{dunk_result.final_rating}",
            100,
            380,
            0.8,
            (255, 180, 0),
            2
        )


        # -----------------------------------
        # GRAPH TITLE
        # -----------------------------------

        _put(
            image,
            "STABILITY DURING DUNK",
            300,
            435,
            0.9,
            (255, 255, 255),
            2
        )


        # -----------------------------------
        # GRAPH
        # -----------------------------------

        draw_stability_graph(
            image,
            stability_times,
            stability_values,
            x0=100,
            y0=455,
            width=700,
            height=230
        )


    else:

        _put(
            image,
            "No completed dunk recorded.",
            220,
            250,
            0.9,
            (0, 0, 255),
            2
        )


    # -----------------------------------
    # EXIT MESSAGE
    # -----------------------------------

    _put(
        image,
        "Press ESC to exit",
        340,
        735,
        0.7,
        (220, 220, 220),
        2
    )


    # -----------------------------------
    # RESULT WINDOW
    # -----------------------------------

    cv2.namedWindow(
        "Dunk Result"
    )

    cv2.imshow(
        "Dunk Result",
        image
    )


    # Keep result screen until ESC
    while True:

        key = cv2.waitKey(50) & 0xFF

        if key == 27:

            break