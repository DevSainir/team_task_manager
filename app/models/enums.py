import enum


class PriorityEnum(str, enum.Enum):
    """Enumeration for task priorities."""

    low = "low"
    medium = "medium"
    high = "high"
