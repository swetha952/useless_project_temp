import math


def calculate_stability(
    immersion,
    duration,
    angle,
    movement
):
    """
    Returns biscuit stability from 0 to 100.

    100 = very stable
    0   = very unstable
    """

    if angle is None:
        angle = 0.0

    # Deeper dunk = more stress
    depth_penalty = max(0, immersion - 40) * 0.6

    # Longer dunk = more stress
    time_penalty = max(0, duration - 2.5) * 4.0

    # Large tilt = more stress
    angle_penalty = abs(angle) * 0.45

    # Sudden movement = more stress
    movement_penalty = movement * 1.2

    stability = (
        100
        - depth_penalty
        - time_penalty
        - angle_penalty
        - movement_penalty
    )

    return max(0.0, min(100.0, stability))