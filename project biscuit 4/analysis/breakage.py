import math


def predict_breakage(
    immersion,
    duration,
    angle,
    movement,
    stability
):
    """
    Estimate breakage probability from 0 to 100%.
    Prototype heuristic model.
    """

    if angle is None:
        angle = 0.0

    risk = (
        0.035 * immersion
        + 0.45 * max(0, duration - 2.5)
        + 0.045 * abs(angle)
        + 0.15 * movement
        - 0.035 * stability
    )

    probability = 1.0 / (
        1.0 + math.exp(-risk + 3.0)
    )

    probability *= 100

    return max(0.0, min(100.0, probability))