from Backend.Routing.intent import Intent
from Backend.Routing.rule_router import RuleRouter
from Backend.Routing.llm_router import LLMRouter


class IntentRouter:
    """
    Hybrid intent router.

    1. First attempts rule-based classification.
    2. Falls back to LLM classification when uncertain.
    """

    def __init__(self):

        self.rule_router = RuleRouter()

        self.llm_router = LLMRouter()

    def route(
            self,
            message: str
    ) -> Intent:
        """
        Route the user's message to the correct intent.
        """

        intent = self.rule_router.route(
            message
        )

        if intent != Intent.UNKNOWN:

            return intent

        return self.llm_router.route(
            message
        )