def calculate_dunk_score(
    duration,
    immersion,
    angle,
    movement,
    stability
):

    if angle is None:
        angle = 0.0

    # Ideal dunk parameters
    ideal_time = 2.5
    ideal_immersion = 50.0
    ideal_angle = 0.0

    time_score = max(
        0,
        100 - abs(duration - ideal_time) * 25
    )

    immersion_score = max(
        0,
        100 - abs(immersion - ideal_immersion) * 2
    )

    angle_score = max(
        0,
        100 - abs(angle - ideal_angle) * 3
    )

    movement_score = max(
        0,
        100 - movement * 5
    )

    score = (
        time_score * 0.25
        + immersion_score * 0.25
        + angle_score * 0.15
        + movement_score * 0.15
        + stability * 0.20
    )

    return max(0, min(100, score))


def get_dunk_rating(score):

    if score >= 85:
        return "മികച്ച ഡങ്ക്"

    elif score >= 65:
        return "അപകടസാധ്യതയുള്ള ഡങ്ക്"

    elif score >= 40:
        return "ബിസ്‌ക്കറ്റിനോടുള്ള അതിക്രമം"

    else:
        return "വൻ ദുരന്ത ഡങ്ക്"