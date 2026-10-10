import pytest
from uuid import uuid4
from pydantic import BaseModel

import Backend.services.auth_service as auth_module

from Backend.memory.postgres_memory import PostgresMemory
from Backend.database.sessions_table import Session as DBSession


# ---------------------------------------------------------
# Test object similar to the custom Insight objects
# that previously caused JSON serialization errors.
# ---------------------------------------------------------
class SampleInsight(BaseModel):
    title: str
    description: str

@pytest.fixture
def analysis_user(
    test_db,
    monkeypatch
):
    monkeypatch.setattr(
        auth_module,
        "EMAIL_VERIFICATION_ENABLED",
        False
    )

    memory = PostgresMemory(
        db=test_db
    )

    auth_service = auth_module.AuthService(
        postgres_memory=memory
    )

    identifier = uuid4().hex[:12]

    user = auth_service.register(
        username=f"analysisuser{identifier}",
        email=f"analysis{identifier}@gmail.com",
        password="TestPassword123!"
    )

    session = DBSession(
        user_id=user.id,
        title="Analysis Integration Test",
        ticker="TSLA"
    )

    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)

    return {
        "user": user,
        "session": session
    }


# ---------------------------------------------------------
# TEST 1
# Save complete investment analysis
# ---------------------------------------------------------

@pytest.mark.integration
def test_save_analysis(
    test_db,
    analysis_user
):

    memory = PostgresMemory(
        db=test_db
    )

    analysis_data = {
        "query": "Analyse Tesla",

        "ticker": "TSLA",

        "company_name": "Tesla, Inc.",

        "market_analysis": {
            "rsi": 52.5,
            "macd": {
                "macd": 3.2,
                "signal": 2.8
            }
        },

        "fundamentals_analysis": {
            "sector": "Consumer Cyclical",
            "pe_ratio": 50.0
        },

        "news_analysis": [
            {
                "headline": "Tesla test headline",
                "sentiment": "positive"
            }
        ],

        "strategy_analysis": {
            "risks": [
                "High valuation"
            ]
        },

        "llm_report": (
            "Tesla test investment report."
        )
    }

    analysis = memory.save_analysis(
        session_id=analysis_user[
            "session"
        ].id,
        user_id=analysis_user[
            "user"
        ].id,
        analysis_data=analysis_data
    )

    assert analysis is not None
    assert analysis.id is not None

    assert analysis.ticker == "TSLA"

    assert (
        analysis.query
        == "Analyse Tesla"
    )

    assert (
        analysis.company_name
        == "Tesla, Inc."
    )

    assert (
        analysis.market_analysis[
            "rsi"
        ]
        == 52.5
    )

    assert (
        analysis.llm_report
        == "Tesla test investment report."
    )

    assert analysis.created_at is not None


# ---------------------------------------------------------
# TEST 2
# JSONB fields accept serializable nested structures
# ---------------------------------------------------------

@pytest.mark.integration
def test_analysis_jsonb_serialization(
    test_db,
    analysis_user
):

    memory = PostgresMemory(
        db=test_db
    )

    insight = SampleInsight(
        title="Debt Risk",
        description=(
            "Debt burden is increasing."
        )
    )

    analysis_data = {
        "query": "Analyse Tesla",

        "ticker": "TSLA",

        "company_name": "Tesla, Inc.",

        "market_analysis": {},

        "fundamentals_analysis": {},

        "news_analysis": [],

        "strategy_analysis": {
            "insights": [
                insight
            ]
        },

        "llm_report": "Test report."
    }

    analysis = memory.save_analysis(
        session_id=analysis_user[
            "session"
        ].id,
        user_id=analysis_user[
            "user"
        ].id,
        analysis_data=analysis_data
    )

    assert analysis is not None

    assert (
        analysis.strategy_analysis[
            "insights"
        ][0]["title"]
        == "Debt Risk"
    )


# ---------------------------------------------------------
# TEST 3
# Missing ticker is rejected
# ---------------------------------------------------------

@pytest.mark.integration
def test_analysis_requires_ticker(
    test_db,
    analysis_user
):

    memory = PostgresMemory(
        db=test_db
    )

    analysis_data = {
        "query": "Analyse Tesla",
        "ticker": None,
        "company_name": "Tesla, Inc.",
        "market_analysis": {},
        "fundamentals_analysis": {},
        "news_analysis": [],
        "strategy_analysis": {},
        "llm_report": "Test report."
    }

    with pytest.raises(
        ValueError,
        match="Analysis ticker is required"
    ):
        memory.save_analysis(
            session_id=analysis_user[
                "session"
            ].id,
            user_id=analysis_user[
                "user"
            ].id,
            analysis_data=analysis_data
        )


# ---------------------------------------------------------
# TEST 4
# Missing query is rejected
# ---------------------------------------------------------

@pytest.mark.integration
def test_analysis_requires_query(
    test_db,
    analysis_user
):

    memory = PostgresMemory(
        db=test_db
    )

    analysis_data = {
        "query": None,
        "ticker": "TSLA",
        "company_name": "Tesla, Inc.",
        "market_analysis": {},
        "fundamentals_analysis": {},
        "news_analysis": [],
        "strategy_analysis": {},
        "llm_report": "Test report."
    }

    with pytest.raises(
        ValueError,
        match="Analysis query is required"
    ):
        memory.save_analysis(
            session_id=analysis_user[
                "session"
            ].id,
            user_id=analysis_user[
                "user"
            ].id,
            analysis_data=analysis_data
        )