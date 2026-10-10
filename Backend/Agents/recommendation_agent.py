from Backend.data_providers.candidate_provider import (
    YahooFinanceCandidateProvider
)


candidate_provider = YahooFinanceCandidateProvider()


def recommendation_candidate_agent(state):
    """
    Discover candidate stocks for the recommendation workflow.

    This agent does not perform market, fundamental, news,
    risk, sentiment, or strategy analysis.
    """

    candidates = candidate_provider.get_candidates(
        limit=10
    )

    return{ "recommendation_candidates" :candidates}

