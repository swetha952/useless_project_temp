"""
Automatic dunk timer.

This module only handles dunk timing and state.
It does not detect the biscuit or calculate immersion.

main.py should pass a simple boolean:
    immersed = immersion > 0
"""

import time


# How long the biscuit must stay immersed / above the surface
# before we accept the change. This reduces tracker jitter.
DEBOUNCE_SECONDS = 0.2


class DunkTimer:
    """
    Simple state-based dunk timer.

    Internal states:
        ABOVE -> ENTERING -> IMMERSED -> EXITING -> COMPLETED

    ENTERING and EXITING are short debounce states so tiny tracker
    movement around the beverage surface does not start/stop the timer.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Return the timer to a fresh ABOVE state (used when R is pressed)."""

        # Current internal state name
        self.state = "ABOVE"

        # When the current dunk started (perf_counter timestamp)
        self._start_time = None

        # Frozen duration after a dunk ends (seconds)
        self._elapsed = 0.0

        # When the current ENTERING or EXITING candidate started
        self._candidate_since = None

        # True while a dunk is confirmed and still in progress
        self._running = False

        # True after at least one dunk has finished (until a new dunk starts)
        self._has_completed = False

    def update(self, immersed):
        """
        Update timer state.

        immersed: True if the biscuit is currently below the beverage
                  surface (immersion > 0), otherwise False.
        """

        now = time.perf_counter()

        if self.state == "ABOVE":
            self._update_above(immersed, now)

        elif self.state == "ENTERING":
            self._update_entering(immersed, now)

        elif self.state == "IMMERSED":
            self._update_immersed(immersed, now)

        elif self.state == "EXITING":
            self._update_exiting(immersed, now)

        elif self.state == "COMPLETED":
            self._update_completed(immersed, now)

    def _update_above(self, immersed, now):
        """Biscuit is above the drink. Timer is not running."""

        if immersed:
            # Might be entering — wait a short time to confirm.
            self.state = "ENTERING"
            self._candidate_since = now
        else:
            self._candidate_since = None

    def _update_entering(self, immersed, now):
        """Biscuit looks immersed, but we are still confirming."""

        if not immersed:
            # Jitter / false start — go back to the previous stable state.
            if self._has_completed:
                self.state = "COMPLETED"
            else:
                self.state = "ABOVE"

            self._candidate_since = None
            return

        held_long_enough = (
            now - self._candidate_since
        ) >= DEBOUNCE_SECONDS

        if held_long_enough:
            # Confirmed dunk. Start a new independent timer.
            self.state = "IMMERSED"
            self._start_time = now
            self._elapsed = 0.0
            self._running = True
            self._has_completed = False
            self._candidate_since = None

    def _update_immersed(self, immersed, now):
        """Confirmed dunk. Keep the timer running."""

        self._elapsed = now - self._start_time

        if not immersed:
            # Might be exiting — wait a short time to confirm.
            self.state = "EXITING"
            self._candidate_since = now

    def _update_exiting(self, immersed, now):
        """Biscuit looks above the drink, but we are still confirming."""

        if immersed:
            # Jitter — still dunking, keep the original start time.
            self.state = "IMMERSED"
            self._candidate_since = None
            self._elapsed = now - self._start_time
            return

        held_long_enough = (
            now - self._candidate_since
        ) >= DEBOUNCE_SECONDS

        if held_long_enough:
            # Confirmed exit. Freeze duration at the first "above" moment
            # so the 0.2s debounce is not added to dunk time.
            self.state = "COMPLETED"
            self._running = False
            self._has_completed = True
            self._elapsed = self._candidate_since - self._start_time
            self._candidate_since = None
        else:
            # Not confirmed yet. Show the time from when it first left.
            self._elapsed = self._candidate_since - self._start_time

    def _update_completed(self, immersed, now):
        """Dunk finished. Keep the last duration until a new dunk starts."""

        if immersed:
            # New dunk may be starting. Confirm with the same debounce.
            self.state = "ENTERING"
            self._candidate_since = now
        else:
            self._candidate_since = None

    def get_elapsed_time(self):
        """Return the current dunk duration in seconds."""

        # Duration is updated inside update() so the clock only
        # moves while we still have biscuit + beverage data.
        return self._elapsed

    def is_running(self):
        """True while a dunk is confirmed and not yet completed."""

        return self._running and self.state in ("IMMERSED", "EXITING")

    def get_ui_status(self):
        """
        Status text for the OpenCV window.

        Possible values: ABOVE, DUNKING, COMPLETED
        """

        if self.state in ("IMMERSED", "EXITING"):
            return "DUNKING"

        if self.state == "COMPLETED":
            return "COMPLETED"

        # ENTERING after a finished dunk should still look COMPLETED
        # until the new dunk is confirmed. This avoids flicker.
        if self.state == "ENTERING" and self._has_completed:
            return "COMPLETED"

        return "ABOVE"