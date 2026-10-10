from typing import List


class ContextBuilder:
    """
    Builds a formatted context string from retrieved analyses.
    This context is injected into the LLM prompt.
    """

    def build(
            self,
            contexts: List[dict]
    ) -> str:
        """
        Convert retrieved analyses into a readable context block.

        Parameters
        ----------
        contexts : List[dict]
            Output returned by VectorMemory.search_similar().

        Returns
        -------
        str
            Formatted context for the PromptBuilder.
        """

        if not contexts:
            return ""

        sections = [
            "## Relevant Previous Analyses\n"
        ]

        for index, context in enumerate(
                contexts,
                start=1
        ):

            similarity = round(
                context["score"] * 100,
                1
            )

            created_at = context["created_at"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            sections.append(

                f"""
--------------------------------------------------

Analysis #{index}

Date:
{created_at}

Similarity:
{similarity}%

Previous Report:

{context["embedded_text"]}

"""

            )

        return "\n".join(sections)