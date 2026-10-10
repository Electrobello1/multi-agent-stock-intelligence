from Backend.Routing.intent import Intent


ALLOWED_RECOMMENDATIONS = {
    "Strong Buy",
    "Buy",
    "Hold",
    "Sell",
    "Strong Sell"
}


REQUIRED_REPORT_SECTIONS = [
    "Executive Summary",
    "Technical Analysis",
    "Fundamental Analysis",
    "News Analysis",
    "Risks",
    "Investor Suitability",
    "Final Recommendation"
]


def validate_llm_output(
    response: str,
    intent: Intent
) -> str:
    """
    Central output-validation entry point.

    The validator selected depends on the current
    application intent.
    """

    response = _validate_basic_response(
        response
    )

    if intent == Intent.REPORT:

        return validate_report(
            response
        )

    if intent == Intent.CHAT:

        return validate_chat(
            response
        )

    if intent == Intent.RECOMMEND:

        return validate_recommendation(
            response
        )

    raise ValueError(
        f"Unsupported intent for output validation: "
        f"{intent}"
    )


def _validate_basic_response(
    response: str
) -> str:
    """
    Common validation applied to every LLM response.
    """

    if response is None:

        raise ValueError(
            "LLM returned no response."
        )

    if not isinstance(response, str):

        raise ValueError(
            "LLM response must be text."
        )

    response = response.strip()

    if not response:

        raise ValueError(
            "LLM returned an empty response."
        )

    return response


def validate_report(
    response: str
) -> str:
    """
    Validate an investment report.

    The report must contain the sections defined
    by the report prompt.
    """

    missing_sections = []

    for section in REQUIRED_REPORT_SECTIONS:

        if section.lower() not in response.lower():

            missing_sections.append(
                section
            )

    if missing_sections:

        raise ValueError(
            "LLM report is missing required sections: "
            + ", ".join(missing_sections)
        )

    recommendation = (
        _extract_final_recommendation(
            response
        )
    )

    if recommendation is not None:

        if recommendation not in ALLOWED_RECOMMENDATIONS:

            raise ValueError(
                "Invalid final recommendation: "
                f"{recommendation}"
            )

    return response


def validate_chat(
    response: str
) -> str:
    """
    Validate a conversational response.

    Chat responses are intentionally less restrictive
    than investment reports.
    """

    if len(response.strip()) < 2:

        raise ValueError(
            "LLM chat response is too short."
        )

    return response


def validate_recommendation(
    response: str
) -> str:
    """
    Validate a recommendation response.

    The current recommendation workflow primarily
    performs candidate discovery rather than making
    a final Buy/Sell decision with the LLM.

    Therefore, only basic validation is applied here.
    """

    if len(response.strip()) < 2:

        raise ValueError(
            "LLM recommendation response is too short."
        )

    return response


def _extract_final_recommendation(
    response: str
):
    """
    Attempt to find the final recommendation in
    the report.

    Returns None when no recognizable recommendation
    is found.
    """

    text = response.lower()

    for recommendation in ALLOWED_RECOMMENDATIONS:

        if recommendation.lower() in text:

            return recommendation

    return None