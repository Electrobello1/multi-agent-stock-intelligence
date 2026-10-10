import pytest

from Backend.Routing.intent import Intent

from Backend.graph.Graph import build_graph


@pytest.mark.integration
def test_complete_report_workflow():

    calls = []

    # -----------------------------------------------------
    # Intent
    # -----------------------------------------------------

    def fake_intent_node(state):

        calls.append(
            "intent_router"
        )

        return {
            "intent": Intent.REPORT
        }

    # -----------------------------------------------------
    # Asset resolution
    # -----------------------------------------------------

    def fake_asset_node(state):

        calls.append(
            "asset_resolver"
        )

        assert state["query"] == (
            "Analyse Tesla"
        )

        return {
            "resolved_asset": {
                "ticker": "TSLA",
                "company_name": (
                    "Tesla, Inc."
                )
            }
        }

    # -----------------------------------------------------
    # Market analysis
    # -----------------------------------------------------

    def fake_market_node(state):

        calls.append(
            "market"
        )

        assert (
            state["resolved_asset"][
                "ticker"
            ]
            == "TSLA"
        )

        return {
            "market_analysis": {
                "rsi": 52.5,
                "macd": {
                    "macd": 3.2,
                    "signal": 2.8
                }
            }
        }

    # -----------------------------------------------------
    # Fundamentals
    # -----------------------------------------------------

    def fake_fundamentals_node(state):

        calls.append(
            "fundamentals"
        )

        return {
            "fundamentals_analysis": {
                "company_name": (
                    "Tesla, Inc."
                ),
                "sector": (
                    "Consumer Cyclical"
                ),
                "pe_ratio": 50.0
            }
        }

    # -----------------------------------------------------
    # News
    # -----------------------------------------------------

    def fake_news_node(state):

        calls.append(
            "news"
        )

        return {
            "news_analysis": [
                {
                    "headline": (
                        "Tesla test headline"
                    ),
                    "sentiment": (
                        "positive"
                    )
                }
            ]
        }

    # -----------------------------------------------------
    # Strategy
    # -----------------------------------------------------

    def fake_strategy_node(state):

        calls.append(
            "strategy"
        )

        # This is important.
        #
        # Strategy must not execute until
        # ALL three parallel nodes completed.

        assert (
            "market_analysis"
            in state
        )

        assert (
            "fundamentals_analysis"
            in state
        )

        assert (
            "news_analysis"
            in state
        )

        return {
            "strategy_analysis": {
                "risks": [
                    "High valuation"
                ],
                "strengths": [
                    "Strong market presence"
                ]
            }
        }

    # -----------------------------------------------------
    # LLM report
    # -----------------------------------------------------

    def fake_report_node(state):

        calls.append(
            "llm_report"
        )

        assert (
            "strategy_analysis"
            in state
        )

        return {
            "llm_report": (
                "Mock Tesla investment report."
            )
        }

    # -----------------------------------------------------
    # Memory
    # -----------------------------------------------------

    def fake_memory_node(state):

        calls.append(
            "memory"
        )

        assert state[
            "llm_report"
        ] == (
            "Mock Tesla investment report."
        )

        # Side-effect node.
        return {}

    # -----------------------------------------------------
    # These branches must NOT execute
    # -----------------------------------------------------

    def unexpected_node(state):

        raise AssertionError(
            "Unexpected graph branch executed."
        )

    # -----------------------------------------------------
    # Build graph using production topology
    # -----------------------------------------------------

    graph =  build_graph(
        intent_node=fake_intent_node,
        asset_node=fake_asset_node,
        market_node=fake_market_node,
        fundamentals_node=(
            fake_fundamentals_node
        ),
        news_node=fake_news_node,
        strategy_node=fake_strategy_node,
        memory_node=fake_memory_node,
        report_node=fake_report_node,
        chat_node=unexpected_node,
        conversation_memory_node=(
            unexpected_node
        ),
        save_chat_node=unexpected_node,
        recommendation_node=unexpected_node,
    )

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    result = graph.invoke(
        {
            "query": "Analyse Tesla",
            "user_id": "test-user",
            "session_id": "test-session"
        }
    )

    # -----------------------------------------------------
    # Validate final state
    # -----------------------------------------------------

    assert (
        result["intent"]
        == Intent.REPORT
    )

    assert (
        result["resolved_asset"][
            "ticker"
        ]
        == "TSLA"
    )

    assert (
        result["market_analysis"][
            "rsi"
        ]
        == 52.5
    )

    assert (
        result[
            "fundamentals_analysis"
        ]["company_name"]
        == "Tesla, Inc."
    )

    assert (
        result["news_analysis"][0][
            "sentiment"
        ]
        == "positive"
    )

    assert (
        result[
            "strategy_analysis"
        ]["risks"][0]
        == "High valuation"
    )

    assert result[
        "llm_report"
    ] == (
        "Mock Tesla investment report."
    )

    # -----------------------------------------------------
    # Verify important nodes executed exactly once
    # -----------------------------------------------------

    assert calls.count(
        "intent_router"
    ) == 1

    assert calls.count(
        "asset_resolver"
    ) == 1

    assert calls.count(
        "market"
    ) == 1

    assert calls.count(
        "fundamentals"
    ) == 1

    assert calls.count(
        "news"
    ) == 1

    assert calls.count(
        "strategy"
    ) == 1

    assert calls.count(
        "llm_report"
    ) == 1

    assert calls.count(
        "memory"
    ) == 1