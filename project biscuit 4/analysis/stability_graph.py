import cv2


def draw_stability_graph(
    frame,
    times,
    values,
    x0=None,
    y0=None,
    width=330,
    height=200
):
    """
    Draw the stability graph.

    This function is now used ONLY on the
    final result screen.
    """

    if len(values) < 2:
        return


    # -----------------------------------
    # DEFAULT POSITION
    # -----------------------------------

    if x0 is None:

        x0 = frame.shape[1] - width - 30


    if y0 is None:

        y0 = 80


    # -----------------------------------
    # GRAPH BACKGROUND
    # -----------------------------------

    cv2.rectangle(
        frame,
        (x0, y0),
        (x0 + width, y0 + height),
        (255, 255, 255),
        2
    )


    # -----------------------------------
    # TITLE
    # -----------------------------------

    cv2.putText(
        frame,
        "BISCUIT STABILITY",
        (x0 + 15, y0 + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    # -----------------------------------
    # GRAPH AREA
    # -----------------------------------

    graph_left = x0 + 50
    graph_right = x0 + width - 15

    graph_top = y0 + 45
    graph_bottom = y0 + height - 30


    # -----------------------------------
    # Y AXIS
    # -----------------------------------

    cv2.line(
        frame,
        (graph_left, graph_top),
        (graph_left, graph_bottom),
        (180, 180, 180),
        1
    )


    # -----------------------------------
    # X AXIS
    # -----------------------------------

    cv2.line(
        frame,
        (graph_left, graph_bottom),
        (graph_right, graph_bottom),
        (180, 180, 180),
        1
    )


    # -----------------------------------
    # Y LABELS
    # -----------------------------------

    cv2.putText(
        frame,
        "100",
        (x0 + 5, graph_top + 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1
    )


    cv2.putText(
        frame,
        "50",
        (x0 + 15, (graph_top + graph_bottom) // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1
    )


    cv2.putText(
        frame,
        "0",
        (x0 + 25, graph_bottom + 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1
    )


    # -----------------------------------
    # TIME
    # -----------------------------------

    cv2.putText(
        frame,
        "TIME",
        (
            graph_right - 40,
            graph_bottom + 22
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1
    )


    # -----------------------------------
    # MAX TIME
    # -----------------------------------

    max_time = max(times)

    if max_time <= 0:

        max_time = 1


    # -----------------------------------
    # CREATE GRAPH POINTS
    # -----------------------------------

    points = []


    for t, value in zip(times, values):

        # Keep stability inside 0-100
        value = max(
            0,
            min(100, value)
        )


        px = int(
            graph_left
            + (t / max_time)
            * (graph_right - graph_left)
        )


        py = int(
            graph_bottom
            - (value / 100)
            * (graph_bottom - graph_top)
        )


        points.append(
            (px, py)
        )


    # -----------------------------------
    # DRAW STABILITY LINE
    # -----------------------------------

    for i in range(1, len(points)):

        cv2.line(
            frame,
            points[i - 1],
            points[i],
            (0, 255, 255),
            3
        )


    # -----------------------------------
    # FINAL POINT
    # -----------------------------------

    if points:

        cv2.circle(
            frame,
            points[-1],
            5,
            (0, 255, 255),
            -1
        )