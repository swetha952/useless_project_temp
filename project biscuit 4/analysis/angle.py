"""
Real-time biscuit orientation from the CSRT tracking box.

Contours are found only inside the tracking ROI so a hand in the
rest of the frame is ignored.

Angle measurement is meant to run only while a dunk is active.
main.py starts and stops this detector from the dunk timer.
"""

import math

import cv2
import numpy as np


# Ignore contours smaller than this fraction of the (inset) ROI.
MIN_AREA_RATIO = 0.08

# Ignore contours smaller than this many pixels, even in a small ROI.
MIN_AREA_PIXELS = 80

# Moving-average length (short so the angle still follows rotation).
HISTORY_SIZE = 7

# Ignore a single sudden jump unless it repeats (hand / background flicker).
MAX_JUMP_DEGREES = 40

# Orientation line length as a fraction of the tracking box.
LINE_LENGTH_RATIO = 0.45

# Shrink the CSRT box slightly so fingers at the edge are ignored.
ROI_INSET_RATIO = 0.12


def _clamp_box(frame, tracking_box):
    """Keep the CSRT box inside the frame."""

    frame_h, frame_w = frame.shape[:2]

    x, y, w, h = [
        int(v)
        for v in tracking_box
    ]

    x = max(0, x)
    y = max(0, y)
    w = max(1, w)
    h = max(1, h)

    if x + w > frame_w:
        w = frame_w - x

    if y + h > frame_h:
        h = frame_h - y

    if w <= 1 or h <= 1:
        return None

    return (x, y, w, h)


def _inset_box(box):
    """
    Shrink the tracking box.

    The biscuit is usually in the middle of the CSRT ROI.
    The hand often sits on the top or side edge.
    """

    x, y, w, h = box

    inset_x = max(3, int(w * ROI_INSET_RATIO))
    inset_y = max(3, int(h * ROI_INSET_RATIO))

    new_x = x + inset_x
    new_y = y + inset_y
    new_w = w - (2 * inset_x)
    new_h = h - (2 * inset_y)

    if new_w < 16 or new_h < 16:
        return box

    return (new_x, new_y, new_w, new_h)


def _wrap_angle(angle):
    """Wrap an orientation into (-90, 90]."""

    while angle > 90:
        angle -= 180

    while angle <= -90:
        angle += 180

    return angle


def _angle_from_min_area_rect(rect):
    """
    Long-axis angle from minAreaRect, using the box corners.

    OpenCV's stored angle field is easy to misread (width/height swap).
    Measuring the longest edge with atan2 is consistent:
        0°   = horizontal biscuit
        +90° = vertical biscuit
        +30° = tilted down-right in image coordinates
    """

    points = cv2.boxPoints(rect)

    edge_a = points[1] - points[0]
    edge_b = points[2] - points[1]

    length_a = float(np.hypot(edge_a[0], edge_a[1]))
    length_b = float(np.hypot(edge_b[0], edge_b[1]))

    if length_a >= length_b:
        dx, dy = float(edge_a[0]), float(edge_a[1])
        long_side = length_a
        short_side = length_b
    else:
        dx, dy = float(edge_b[0]), float(edge_b[1])
        long_side = length_b
        short_side = length_a

    angle = math.degrees(math.atan2(dy, dx))

    return _wrap_angle(angle), long_side, short_side


def _circular_mean(angles):
    """
    Average angles that wrap at ±90°.

    A biscuit at 89° is almost the same as -89°, so a normal mean
    would be wrong. Doubling maps 180° orientation to a full circle.
    """

    if not angles:
        return None

    doubled = [
        math.radians(angle) * 2
        for angle in angles
    ]

    mean_sin = sum(math.sin(value) for value in doubled) / len(doubled)
    mean_cos = sum(math.cos(value) for value in doubled) / len(doubled)

    mean_angle = math.degrees(math.atan2(mean_sin, mean_cos)) / 2.0

    return _wrap_angle(mean_angle)


def _wrapped_difference(angle_a, angle_b):
    """Smallest difference between two orientations (0 to 90)."""

    diff = abs(angle_a - angle_b)
    return min(diff, 180.0 - diff)


def _contour_features(contour, roi_shape):
    """Area, centre distance and elongation for one contour."""

    area = cv2.contourArea(contour)

    if area <= 0 or len(contour) < 5:
        return None

    moments = cv2.moments(contour)

    if moments["m00"] <= 0:
        return None

    roi_h, roi_w = roi_shape[:2]
    center_x = roi_w / 2.0
    center_y = roi_h / 2.0

    contour_cx = moments["m10"] / moments["m00"]
    contour_cy = moments["m01"] / moments["m00"]

    dist = math.hypot(
        contour_cx - center_x,
        contour_cy - center_y
    )

    rect = cv2.minAreaRect(contour)
    _angle, long_side, short_side = _angle_from_min_area_rect(rect)

    if short_side < 1:
        return None

    aspect = long_side / short_side

    return {
        "contour": contour,
        "rect": rect,
        "area": area,
        "dist": dist,
        "aspect": aspect
    }


def _score_contour(features, roi_shape):
    """
    Higher scores are more biscuit-like.

    Prefer a centred, elongated blob. Round hand-like blobs score low.
    """

    roi_h, roi_w = roi_shape[:2]
    max_dist = math.hypot(roi_w / 2.0, roi_h / 2.0)

    if max_dist < 1:
        max_dist = 1.0

    center_score = 1.0 - (features["dist"] / max_dist)

    # Biscuits are usually longer than they are thick.
    aspect = features["aspect"]
    if aspect < 1.2:
        elongation = 0.15
    elif aspect > 8.0:
        elongation = 0.4
    else:
        elongation = min((aspect - 1.0) / 3.0, 1.0)

    area_score = min(
        features["area"] / float(roi_w * roi_h),
        1.0
    )

    return (
        (0.40 * center_score)
        + (0.45 * elongation)
        + (0.15 * area_score)
    )


def _pick_biscuit_rect(contours, roi_shape):
    """Choose the minAreaRect most likely to be the biscuit."""

    roi_h, roi_w = roi_shape[:2]
    roi_area = float(roi_w * roi_h)
    min_area = max(MIN_AREA_PIXELS, roi_area * MIN_AREA_RATIO)

    best_rect = None
    best_score = -1.0

    for contour in contours:

        features = _contour_features(contour, roi_shape)

        if features is None:
            continue

        if features["area"] < min_area:
            continue

        score = _score_contour(features, roi_shape)

        if score > best_score:
            best_score = score
            best_rect = features["rect"]

    return best_rect, best_score


def _binary_masks(gray):
    """
    Build two candidate masks: Otsu as-is, and Otsu inverted.

    One of these usually makes the biscuit white against a dark
    background. We try both and keep the better contour.
    """

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    _, otsu = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    inverted = cv2.bitwise_not(otsu)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (5, 5)
    )

    masks = []

    for mask in (otsu, inverted):

        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
        masks.append(cleaned)

    return masks


def _raw_angle_from_roi(roi):
    """
    Measure one frame of biscuit orientation inside the ROI.

    Returns the raw (unsmoothed) angle, or None if detection failed.
    """

    if roi is None or roi.size == 0:
        return None

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(4, 4)
    )
    gray = clahe.apply(gray)

    best_rect = None
    best_score = -1.0

    for mask in _binary_masks(gray):

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            continue

        rect, score = _pick_biscuit_rect(contours, roi.shape)

        if rect is None:
            continue

        if score > best_score:
            best_score = score
            best_rect = rect

    if best_rect is None:
        return None

    angle, long_side, short_side = _angle_from_min_area_rect(best_rect)

    if long_side < 1 or short_side < 1:
        return None

    return angle


class BiscuitAngleDetector:
    """
    Tracks a short history of valid biscuit angles.

    Failed frames keep the last good angle instead of jumping to 0.
    Measurement only updates while start_measuring() is active.
    """

    def __init__(self, history_size=HISTORY_SIZE):
        self.history_size = history_size
        self.reset()

    def reset(self):
        """Clear history and the last angle (used when R is pressed)."""

        self._history = []
        self._last_angle = None
        self._active = False
        self._pending_jumps = []

    def start_measuring(self):
        """Begin angle measurement for a new dunk."""

        self._history = []
        self._last_angle = None
        self._active = True
        self._pending_jumps = []

    def stop_measuring(self):
        """
        Stop updating. Keep the last valid angle as the final dunk angle.
        """

        self._active = False
        self._pending_jumps = []

    def is_active(self):
        """True while the dunk timer is running."""

        return self._active

    def calculate_biscuit_angle(self, frame, tracking_box):
        """
        Estimate biscuit orientation from the CSRT box.

        Does nothing (returns the frozen/last angle) when inactive.

        frame: camera image without overlay drawings
        tracking_box: (x, y, w, h) from CSRT
        """

        if not self._active:
            return self._last_angle

        box = _clamp_box(frame, tracking_box)

        if box is None:
            return self._last_angle

        box = _inset_box(box)
        x, y, w, h = box
        roi = frame[y:y + h, x:x + w]

        raw_angle = _raw_angle_from_roi(roi)

        if raw_angle is None:
            # Detection failed — keep the previous valid angle.
            return self._last_angle

        if self._last_angle is not None:

            jump = _wrapped_difference(raw_angle, self._last_angle)

            if jump > MAX_JUMP_DEGREES:
                # One noisy frame (often the hand). Wait for repeats.
                self._pending_jumps.append(raw_angle)

                if len(self._pending_jumps) < 3:
                    return self._last_angle

                raw_angle = _circular_mean(self._pending_jumps)
                self._pending_jumps = []

            else:
                self._pending_jumps = []

        self._history.append(raw_angle)

        if len(self._history) > self.history_size:
            self._history.pop(0)

        smoothed = _circular_mean(self._history)
        self._last_angle = smoothed

        return self._last_angle

    def get_angle(self):
        """Return the last valid smoothed angle, or None."""

        return self._last_angle


def calculate_biscuit_angle(frame, tracking_box, detector=None):
    """
    Convenience wrapper.

    If a detector is passed, history/smoothing is preserved.
    """

    if detector is None:
        detector = BiscuitAngleDetector()
        detector.start_measuring()

    return detector.calculate_biscuit_angle(
        frame,
        tracking_box
    )


def orientation_line_points(center_x, center_y, angle_degrees, box_w, box_h):
    """
    Endpoints of a line through the biscuit centre at the given angle.

    Angle 0° is horizontal. Positive angles tilt toward the
    bottom-right in image coordinates.
    """

    length = int(
        max(box_w, box_h) * LINE_LENGTH_RATIO
    )

    if length < 10:
        length = 10

    radians = math.radians(angle_degrees)

    dx = int(round(length * math.cos(radians)))
    dy = int(round(length * math.sin(radians)))

    start = (
        int(center_x - dx),
        int(center_y - dy)
    )

    end = (
        int(center_x + dx),
        int(center_y + dy)
    )

    return start, end