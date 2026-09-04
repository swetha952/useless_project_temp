import math


class MovementTracker:

    def __init__(self):
        self.reset()

    def reset(self):
        self.previous_x = None
        self.previous_y = None

    def update(self, center_x, center_y):

        if self.previous_x is None:

            self.previous_x = center_x
            self.previous_y = center_y

            return 0.0

        dx = center_x - self.previous_x
        dy = center_y - self.previous_y

        movement = math.sqrt(
            dx * dx + dy * dy
        )

        self.previous_x = center_x
        self.previous_y = center_y

        return movement