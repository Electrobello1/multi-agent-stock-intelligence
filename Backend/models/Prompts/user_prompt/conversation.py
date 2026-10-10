import json


def to_prompt(data):

    return json.dumps(

        data,

        indent=4,

        default=str,

        ensure_ascii=False

    )


def build_conversation_prompt(state):

    return f"""
Investment Report

{state.get("llm_report", "")}


Relevant Previous Analyses

{state.get("retrieved_context", "")}


Conversation History

{to_prompt(state.get("conversation_history", []))}


User Question

{state.get("query", "")}


Answer the user's question using:

1. The investment report.
2. Previous conversation history.
3. Retrieved historical analyses when relevant.

Rules

- Do NOT regenerate the report.
- Explain concepts clearly.
- If calculations are involved, show the reasoning.
- Preserve all financial values.
- If the report does not contain the requested information, clearly state that.
- Keep the answer focused on the user's question.
"""