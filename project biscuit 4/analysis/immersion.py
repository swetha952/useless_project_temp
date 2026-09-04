"""
Biscuit immersion from the tracked box and beverage line.

This module calculates the current percentage and records the
maximum reached during a dunk.
"""


def calculate_immersion(biscuit_bottom, biscuit_height, beverage_surface):
    """
    Return how much of the biscuit is below the beverage, 0 to 100.

    biscuit_bottom: y of the bottom of the CSRT box
    biscuit_height: height of the CSRT box
    beverage_surface: y of the calibrated beverage line
    """

    if beverage_surface is None:
        return 0.0

    if biscuit_height is None or biscuit_height <= 0:
        return 0.0

    depth = biscuit_bottom - beverage_surface

    if depth < 0:
        depth = 0

    immersion = (depth / biscuit_height) * 100.0

    if immersion > 100:
        immersion = 100.0

    return immersion


class ImmersionRecorder:
    """
    Remembers the deepest immersion during the current dunk.

    Recording starts when the dunk timer starts and stops when
    the dunk timer stops. The maximum is then frozen.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Clear everything (used when R is pressed)."""

        self.max_immersion = 0.0
        self.recording = False

    def start_dunk(self):
        """Begin a new dunk. Maximum starts at 0 again."""

        self.max_immersion = 0.0
        self.recording = True

    def update(self, current_immersion):
        """Keep the highest immersion seen while recording."""

        if not self.recording:
            return

        if current_immersion > self.max_immersion:
            self.max_immersion = current_immersion

    def stop_dunk(self):
        """Stop recording. Keep the frozen maximum."""

        self.recording = False

    def get_max_immersion(self):
        """Return the highest immersion recorded this dunk."""

        return self.max_immersion