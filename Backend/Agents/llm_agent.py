from Backend.models.LLM import generate_llm_response

from Backend.Routing.intent import Intent

from Backend.models.Prompts.report_prompt import (
    REPORT_SYSTEM_PROMPT
)

from Backend.models.Prompts.conversation_prompt import (
    CHAT_SYSTEM_PROMPT
)

from Backend.models.Prompts.user_prompt.report import (
    build_report_prompt
)


from Backend.models.Prompts.user_prompt.conversation import (
    build_conversation_prompt
)

from Backend.guardrails.output_guardrail import (
    validate_llm_output
)

from Backend.utils.perf_timer import (
    timed_step
)
import logging
logger = logging.getLogger(__name__)
class LLMAgent:

    def run(
        self,
        state,
        intent: Intent
    ):

        # ----------------------------------
        # REPORT
        # ----------------------------------

        if intent == Intent.REPORT:

            system_prompt = (
                REPORT_SYSTEM_PROMPT
            )

            user_prompt = build_report_prompt(
                state
            )

            output_key = "llm_report"

        # ----------------------------------
        # CHAT
        # ----------------------------------

        elif intent == Intent.CHAT:

            system_prompt = (
                CHAT_SYSTEM_PROMPT
            )

            user_prompt = (
                build_conversation_prompt(
                    state
                )
            )

            output_key = "chat_response"

        # ----------------------------------
        # UNSUPPORTED INTENT
        # ----------------------------------

        else:

            raise ValueError(
                f"Unsupported intent: {intent}"
            )

        # ----------------------------------
        # CALL LLM
        # ----------------------------------
        with timed_step(
                logger,
               "llm_generate",
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
          ):
            response = generate_llm_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt
            )

        # ----------------------------------
        # OUTPUT GUARDRAIL
        # ----------------------------------

        response = validate_llm_output(
            response,
            intent
        )

        if not response:
            raise ValueError(
                "LLM returned an empty response."
            )

        # ----------------------------------
        # RETURN ONLY NODE UPDATE
        # ----------------------------------

        return {
            output_key: response
        }