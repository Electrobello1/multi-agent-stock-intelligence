import pytest

from Backend.Agents import asset_agent


@pytest.mark.unit
def test_asset_resolver_returns_correct_key(
    monkeypatch
):

    expected_asset = {
        "ticker": "TSLA",
        "company_name": "Tesla, Inc."
    }

    # Mock the actual ticker resolver.
    monkeypatch.setattr(
        asset_agent.resolver,
        "resolve",
        lambda query: expected_asset
    )

    state = {
        "query": "TSLA"
    }

    result = asset_agent.asset_resolver_agent(
        state
    )

    assert result == {
        "resolved_asset": expected_asset
    }


@pytest.mark.unit
def test_asset_agent_preserves_original_state(
    monkeypatch
):

    monkeypatch.setattr(
        asset_agent.resolver,
        "resolve",
        lambda query: {
            "ticker": "TSLA"
        }
    )

    state = {
        "query": "TSLA",
        "user_id": "123"
    }

    result = asset_agent.asset_resolver_agent(
        state
    )

    assert state["query"] == "TSLA"

    assert state["user_id"] == "123"

    assert list(result.keys()) == [
        "resolved_asset"
    ]