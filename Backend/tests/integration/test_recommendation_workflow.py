import pytest

from Backend.Routing.intent import Intent

from Backend.Agents import recommendation_agent

# Change this only if your graph module has another filename.
from Backend.graph.Graph import build_graph


# =========================================================
# TEST 1
# REAL RECOMMENDATION AGENT + MOCKED YAHOO PROVIDER
# =========================================================

@pytest.mark.integration
def test_real_recommendation_agent_returns_candidates(
    monkeypatch
):

    # -----------------------------------------------------
    # Mock only the external Yahoo provider
    # -----------------------------------------------------

    expected_candidates = [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc."
        },
        {
            "ticker": "MSFT",
            "company_name": "Microsoft Corporation"
        },
        {
            "ticker": "NVDA",
            "company_name": "NVIDIA Corporation"
        }
    ]

    def fake_get_candidates(
        limit
    ):
        assert limit == 10

        return expected_candidates

    monkeypatch.setattr(
        recommendation_agent.candidate_provider,
        "get_candidates",
        fake_get_candidates
    )

    # -----------------------------------------------------
    # Intent
    # -----------------------------------------------------

    def fake_intent_node(state):

        return {
            "intent": Intent.RECOMMEND
        }

    # -----------------------------------------------------
    # Wrong graph branches must not execute
    # -----------------------------------------------------

    def unexpected_node(state):

        raise AssertionError(
            "Unexpected graph branch executed."
        )

    # -----------------------------------------------------
    # Build production topology
    # -----------------------------------------------------

    test_graph = build_graph(
        intent_node=fake_intent_node,

        # REAL recommendation agent
        recommendation_node=(
            recommendation_agent
            .recommendation_candidate_agent
        ),

        asset_node=unexpected_node,
        market_node=unexpected_node,
        fundamentals_node=unexpected_node,
        news_node=unexpected_node,
        strategy_node=unexpected_node,
        report_node=unexpected_node,
        memory_node=unexpected_node,

        conversation_memory_node=(
            unexpected_node
        ),

        chat_node=unexpected_node,

        save_chat_node=unexpected_node,
    )

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    result = test_graph.invoke(
        {
            "query": (
                "Recommend some stocks"
            ),
            "user_id": "test-user",
            "session_id": "test-session"
        }
    )

    # -----------------------------------------------------
    # Assertions
    # -----------------------------------------------------

    assert (
        result["intent"]
        == Intent.RECOMMEND
    )

    assert (
        result[
            "recommendation_candidates"
        ]
        == expected_candidates
    )

    assert len(
        result[
            "recommendation_candidates"
        ]
    ) == 3


# =========================================================
# TEST 2
# EMPTY PROVIDER RESULT
# =========================================================

@pytest.mark.integration
def test_real_recommendation_agent_handles_empty_candidates(
    monkeypatch
):

    monkeypatch.setattr(
        recommendation_agent.candidate_provider,
        "get_candidates",
        lambda limit: []
    )

    def fake_intent_node(state):

        return {
            "intent": Intent.RECOMMEND
        }

    def unexpected_node(state):

        raise AssertionError(
            "Unexpected graph branch executed."
        )

    test_graph = build_graph(
        intent_node=fake_intent_node,

        recommendation_node=(
            recommendation_agent
            .recommendation_candidate_agent
        ),

        asset_node=unexpected_node,
        market_node=unexpected_node,
        fundamentals_node=unexpected_node,
        news_node=unexpected_node,
        strategy_node=unexpected_node,
        report_node=unexpected_node,
        memory_node=unexpected_node,

        conversation_memory_node=(
            unexpected_node
        ),

        chat_node=unexpected_node,

        save_chat_node=unexpected_node,
    )

    result = test_graph.invoke(
        {
            "query": "Find stocks",
            "user_id": "test-user",
            "session_id": "test-session"
        }
    )

    assert (
        result[
            "recommendation_candidates"
        ]
        == []
    )


# =========================================================
# TEST 3
# PROVIDER FAILURE PROPAGATES
# =========================================================

@pytest.mark.integration
def test_real_recommendation_agent_propagates_provider_failure(
    monkeypatch
):

    def failing_provider(
        limit
    ):
        raise RuntimeError(
            "Yahoo candidate provider unavailable."
        )

    monkeypatch.setattr(
        recommendation_agent.candidate_provider,
        "get_candidates",
        failing_provider
    )

    def fake_intent_node(state):

        return {
            "intent": Intent.RECOMMEND
        }

    def unexpected_node(state):

        raise AssertionError(
            "Unexpected graph branch executed."
        )

    test_graph = build_graph(
        intent_node=fake_intent_node,

        recommendation_node=(
            recommendation_agent
            .recommendation_candidate_agent
        ),

        asset_node=unexpected_node,
        market_node=unexpected_node,
        fundamentals_node=unexpected_node,
        news_node=unexpected_node,
        strategy_node=unexpected_node,
        report_node=unexpected_node,
        memory_node=unexpected_node,

        conversation_memory_node=(
            unexpected_node
        ),

        chat_node=unexpected_node,

        save_chat_node=unexpected_node,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Yahoo candidate provider unavailable"
        )
    ):

        test_graph.invoke(
            {
                "query": (
                    "Recommend some stocks"
                ),
                "user_id": "test-user",
                "session_id": "test-session"
            }
        )