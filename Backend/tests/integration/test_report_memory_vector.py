import pytest

from uuid import uuid4

from sqlalchemy.orm import Session

import Backend.services.auth_service as auth_module

from Backend.Routing.intent import Intent
from Backend.memory.postgres_memory import (
    PostgresMemory
)
from Backend.database.sessions_table import (
    Session as DBSession
)
from Backend.database.analysis import Analysis
from Backend.database.Analysis_vector import (
    AnalysisVector
)
from Backend.embeddings.embedding_service import (
    EmbeddingService
)
from Backend.Agents.memory_agent import (
    memory_agent
)


from Backend.graph.Graph import build_graph


# ---------------------------------------------------------
# No-op Redis
#
# Redis is NOT what this test is testing.
# Real Redis gets its own integration tests.
# ---------------------------------------------------------

class NoOpRedisMemory:

    def __getattr__(self, name):

        def no_op(
            *args,
            **kwargs
        ):
            return None

        return no_op


# ---------------------------------------------------------
# USER + SESSION
# ---------------------------------------------------------

@pytest.fixture
def report_test_context(
    test_db,
    monkeypatch
):

    monkeypatch.setattr(
        auth_module,
        "EMAIL_VERIFICATION_ENABLED",
        False
    )

    postgres_memory = PostgresMemory(
        db=test_db
    )

    auth_service = auth_module.AuthService(
        postgres_memory=postgres_memory
    )

    identifier = uuid4().hex[:12]

    user = auth_service.register(
        username=(
            f"reportuser{identifier}"
        ),
        email=(
            f"report{identifier}@gmail.com"
        ),
        password="TestPassword123!"
    )

    session = DBSession(
        user_id=user.id,
        title="Report Vector Test",
        ticker="TSLA"
    )

    test_db.add(
        session
    )

    test_db.commit()

    test_db.refresh(
        session
    )

    return {
        "user": user,
        "session": session
    }


# ---------------------------------------------------------
# COMPLETE REPORT → MEMORY → PGVECTOR
# ---------------------------------------------------------

@pytest.mark.integration
def test_report_persists_analysis_and_vector(
    test_db,
    report_test_context
):

    user = report_test_context[
        "user"
    ]

    session = report_test_context[
        "session"
    ]

    # -----------------------------------------------------
    # Fake upstream nodes
    # -----------------------------------------------------

    def fake_intent_node(state):

        return {
            "intent": Intent.REPORT
        }

    def fake_asset_node(state):

        return {
            "resolved_asset": {
                "ticker": "TSLA",
                "company_name": "Tesla, Inc."
            }
        }

    def fake_market_node(state):

        return {
            "market_analysis": {
                "rsi": 51.5,

                "macd": {
                    "macd": 4.1,
                    "signal": 3.7
                }
            }
        }

    def fake_fundamentals_node(
        state
    ):

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

    def fake_news_node(state):

        return {
            "news_analysis": [
                {
                    "headline": (
                        "Tesla integration "
                        "test headline"
                    ),
                    "sentiment": (
                        "positive"
                    )
                }
            ]
        }

    def fake_strategy_node(state):

        # Prove fan-in completed.
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
                "strengths": [
                    "Strong brand"
                ],
                "risks": [
                    "High valuation"
                ]
            }
        }

    def fake_report_node(state):

        return {
            "llm_report": (
                "Tesla has a strong brand "
                "but carries valuation risk."
            )
        }

    # -----------------------------------------------------
    # DB factory used by the REAL memory_agent
    #
    # Use the pytest transaction's connection,
    # but give memory_agent its own Session so
    # memory_agent.close() does not close test_db.
    # -----------------------------------------------------

    def test_db_factory():

        return Session(
            bind=test_db.connection(),
            autoflush=False,
            expire_on_commit=False,
            join_transaction_mode=(
                "create_savepoint"
            )
        )

    # -----------------------------------------------------
    # REAL MEMORY NODE
    # -----------------------------------------------------

    def real_memory_node(state):

        return memory_agent(
            state,

            db_factory=(
                test_db_factory
            ),

            redis_factory=(
                NoOpRedisMemory
            ),

            # REAL embedding model
            embedding_factory=(
                EmbeddingService
            )
        )

    # -----------------------------------------------------
    # Wrong branches must not execute
    # -----------------------------------------------------

    def unexpected_node(state):

        raise AssertionError(
            "Unexpected graph branch executed."
        )

    # -----------------------------------------------------
    # Build real topology
    # -----------------------------------------------------

    test_graph = build_graph(
        intent_node=fake_intent_node,
        asset_node=fake_asset_node,
        market_node=fake_market_node,
        fundamentals_node=(
            fake_fundamentals_node
        ),
        news_node=fake_news_node,
        strategy_node=fake_strategy_node,
        report_node=fake_report_node,

        # REAL memory agent
        memory_node=real_memory_node,

        chat_node=unexpected_node,
        conversation_memory_node=(
            unexpected_node
        ),
        save_chat_node=unexpected_node,
        recommendation_node=(
            unexpected_node
        ),
    )

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    result = test_graph.invoke(
        {
            "query": "Analyse Tesla",
            "user_id": str(
                user.id
            ),
            "session_id": str(
                session.id
            )
        }
    )

    # -----------------------------------------------------
    # Graph assertions
    # -----------------------------------------------------

    assert (
        result["intent"]
        == Intent.REPORT
    )

    assert result[
        "llm_report"
    ] == (
        "Tesla has a strong brand "
        "but carries valuation risk."
    )

    assert result.get(
        "analysis_id"
    ) is not None

    # -----------------------------------------------------
    # Verify analysis was REALLY persisted
    # -----------------------------------------------------

    analysis = (
        test_db.query(Analysis)
        .filter(
            Analysis.id
            == result["analysis_id"]
        )
        .first()
    )

    assert analysis is not None

    assert (
        analysis.ticker
        == "TSLA"
    )

    assert (
        analysis.query
        == "Analyse Tesla"
    )

    assert (
        analysis.llm_report
        == (
            "Tesla has a strong brand "
            "but carries valuation risk."
        )
    )

    # -----------------------------------------------------
    # Verify pgvector row REALLY exists
    # -----------------------------------------------------

    vector = (
        test_db.query(
            AnalysisVector
        )
        .filter(
            AnalysisVector.analysis_id
            == analysis.id
        )
        .first()
    )

    assert vector is not None

    assert (
        vector.analysis_id
        == analysis.id
    )

    assert (
        vector.user_id
        == user.id
    )

    assert (
        vector.session_id
        == session.id
    )

    assert vector.embedded_text

    # Your BGE model / database column
    # is VECTOR(384).
    assert len(
        vector.embedding
    ) == 384