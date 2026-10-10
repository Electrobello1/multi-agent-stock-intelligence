import pytest

from typing import TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from Backend.Agents import asset_agent


class StockStateForTest(TypedDict, total=False):

    query: str

    resolved_asset: dict

    llm_report: str


@pytest.mark.integration
def test_asset_to_report_handoff(
    monkeypatch
):

    # Mock external asset resolution.
    monkeypatch.setattr(
        asset_agent.resolver,
        "resolve",
        lambda query: {
            "ticker": "TSLA",
            "company_name": "Tesla, Inc."
        }
    )

    # Deterministic downstream report node.
    def fake_report_agent(state):

        ticker = state[
            "resolved_asset"
        ]["ticker"]

        return {
            "llm_report": (
                f"Generated report for {ticker}"
            )
        }

    # Build a small LangGraph integration graph.
    builder = StateGraph(
        StockStateForTest
    )

    builder.add_node(
        "asset_resolver",
        asset_agent.asset_resolver_agent
    )

    builder.add_node(
        "report",
        fake_report_agent
    )

    builder.add_edge(
        START,
        "asset_resolver"
    )

    builder.add_edge(
        "asset_resolver",
        "report"
    )

    builder.add_edge(
        "report",
        END
    )

    graph = builder.compile()

    # Executegraph.
    result = graph.invoke(
        {
            "query": "TSLA"
        }
    )

    # Validate state handoff.
    assert result["query"] == "TSLA"

    assert result["resolved_asset"]["ticker"] == "TSLA"

    assert result["llm_report"] == (
        "Generated report for TSLA"
    )