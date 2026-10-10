from Backend.models.LLM import generate_llm_response
from Backend.Routing.intent import Intent


class LLMRouter:
    """
    Uses the LLM to classify ambiguous user requests.

    This router is only called when the RuleRouter
    cannot confidently determine the user's intent.
    """

    SYSTEM_PROMPT = """
You are an intent classification system.

Your task is to classify the user's request into exactly ONE of
the following categories.

REPORT
The user wants a NEW investment analysis or asks for the price of  a share.

Examples:
- Analyze Tesla
- Evaluate Apple
- Research Microsoft
- Perform a technical analysis of NVIDIA

CHAT
The user is asking questions about an existing report or wants
clarification. 

Examples:
- Explain RSI
- Why did you recommend Buy?
- Clarify the debt analysis
- Explain MACD

RECOMMEND
The user wants investment suggestions.

Examples:
- Recommend a good stock
- Which company should I invest in?
- Suggest dividend stocks
- Give me investment ideas

Return ONLY one word:

REPORT

or

CHAT

or

RECOMMEND

Do not explain your answer.
"""

    def route(
            self,
            message: str
    ) -> Intent:

        response = generate_llm_response(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=message
        )

        response = response.strip().upper()

        if response == "REPORT":
            return Intent.REPORT

        if response == "CHAT":
            return Intent.CHAT

        if response == "RECOMMEND":
            return Intent.RECOMMEND

        return Intent.UNKNOWN