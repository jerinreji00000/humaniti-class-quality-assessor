"""Scoring rubric and deterministic category thresholds."""

DIMENSIONS = [
    "teaching_clarity",
    "lesson_structure",
    "student_engagement_evidence",
    "audio_quality",
    "visual_presentation_evidence",
]

# Weights sum to 1.0. Engagement and visual dimensions must be scored cautiously
# because a transcript-only pipeline cannot establish all relevant evidence.
WEIGHTS = {
    "teaching_clarity": 0.30,
    "lesson_structure": 0.25,
    "student_engagement_evidence": 0.20,
    "audio_quality": 0.15,
    "visual_presentation_evidence": 0.10,
}


def category_from_score(score: float) -> str:
    if score < 2.0:
        return "Poor"
    if score < 3.0:
        return "Average"
    if score < 4.0:
        return "Good"
    return "Excellent"


def weighted_score(dimension_scores: dict) -> float:
    """Calculate a weighted average from valid scores; renormalize for missing scores."""
    total = 0.0
    weight_total = 0.0
    for dimension, weight in WEIGHTS.items():
        item = dimension_scores.get(dimension, {})
        value = item.get("score") if isinstance(item, dict) else None
        if isinstance(value, (int, float)) and 1 <= value <= 5:
            total += float(value) * weight
            weight_total += weight
    if weight_total == 0:
        raise ValueError("The model did not return any valid dimension scores.")
    return round(total / weight_total, 2)
