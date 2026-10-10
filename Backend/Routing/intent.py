from enum import Enum


class Intent(Enum):
    """
    Supported user intents.
    """

    REPORT = "report"

    CHAT = "chat"

    RECOMMEND = "recommend"

    UNKNOWN = "unknown"