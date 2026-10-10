import re

from Backend.Routing.intent import Intent


class RuleRouter:
    """
    Fast rule-based intent classifier.

    This router handles obvious user requests without
    invoking the LLM.
    """

    REPORT_PATTERNS = [

        r"\banaly[sz]e\b",
        r"\banalysis\b",
        r"\bevaluate\b",
        r"\bresearch\b",
        r"\breview\b",
        r"\bvalue\b",
        r"\bperform analysis\b",
        r"\btechnical analysis\b",
        r"\bfundamental analysis\b"

    ]

    CHAT_PATTERNS = [

        r"\bwhy\b",
        r"\bwhat does\b",
        r"\bexplain\b",
        r"\bclarify\b",
        r"\bhow\b",
        r"\bhelp me understand\b",
        r"\bwhat is\b",
        r"\bcan you explain\b"

    ]

    RECOMMEND_PATTERNS = [

        r"\brecommend\b",
        r"\bsuggest\b",
        r"\bwhich stock\b",
        r"\bwhat stock\b",
        r"\bgood investment\b",
        r"\bwhere should i invest\b",
        r"\bwhat should i buy\b",
        r"\bbest stock\b",
        r"\binvest in\b"

    ]

    def route(

            self,

            message: str

    ) -> Intent:

        """
        Classify a message using deterministic rules.
        """

        text = message.lower().strip()

        for pattern in self.RECOMMEND_PATTERNS:

            if re.search(

                    pattern,

                    text

            ):

                return Intent.RECOMMEND

        for pattern in self.REPORT_PATTERNS:

            if re.search(

                    pattern,

                    text

            ):

                return Intent.REPORT

        for pattern in self.CHAT_PATTERNS:

            if re.search(

                    pattern,

                    text

            ):

                return Intent.CHAT

        return Intent.UNKNOWN