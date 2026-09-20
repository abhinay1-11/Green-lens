"""
Confidence normalization utility module for GreenLens.
Ensures score conversion to 0.0-1.0 float and formatted percentage strings.
"""

def normalize_confidence(score: float, is_percentage: bool = False) -> float:
    """
    Normalizes any provider confidence score into a float strictly between 0.0 and 1.0.
    
    If is_percentage is True (or score > 1.0 and is_percentage=True), divides by 100.0.
    Clamps any result strictly to [0.0, 1.0].
    """
    if score is None:
        return 0.0

    val = float(score)

    if is_percentage or (val > 1.0 and is_percentage):
        val = val / 100.0

    return max(0.0, min(1.0, val))


def format_confidence_percentage(score: float) -> str:
    """
    Formats a 0.0-1.0 confidence score into a human-readable percentage string (e.g., "91%").
    Never returns >100% or invalid values.
    """
    normalized = normalize_confidence(score, is_percentage=(score > 1.0 and score <= 100.0))
    pct = round(normalized * 100.0)
    return f"{pct}%"
