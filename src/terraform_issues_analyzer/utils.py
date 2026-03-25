"""Shared utility helpers used across reporting modules."""


def format_age(days: int) -> str:
    """Format age in days to a compact human-readable value.

    Args:
        days: Number of days.

    Returns:
        Age string with day, month, or year suffix.
    """
    if days < 30:
        return f"{days}d"
    if days < 365:
        return f"{days / 30:.1f}mo"
    return f"{days / 365:.1f}y"

