import pytest

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from Backend.api.main import app

from Backend.database.connection import get_db

from Backend.database.sessions_table import (
    Session as DBSession
)

from Backend.database.analysis import Analysis

from Backend.database.Analysis_vector import (
    AnalysisVector
)

from Backend.memory.postgres_memory import (
    PostgresMemory
)

from Backend.services.auth_service import (
    AuthService
)

import Backend.services.auth_service as auth_module

from Backend.embeddings.embedding_service import (
    EmbeddingService
)

from Backend.Agents.memory_agent import (
    memory_agent
)

from Backend.Routing.intent import Intent

from Backend.graph.Graph import build_graph




import Backend.api.routes as chat_route_module


# =========================================================
# REDIS STUB
#
# Redis is deliberately excluded from this E2E test.
# PostgreSQL + pgvector remain REAL.
# =========================================================

class NoOpRedisMemory:

    def __getattr__(self, name):

        def no_op(
            *args,
            **kwargs
        ):
            return None

        return no_op


# =========================================================
# AUTHENTICATED REPORT E2E
#
# HTTP
#   ↓
# FastAPI
#   ↓
# JWT authentication
#   ↓
# /chat
#   ↓
# LangGraph
#   ↓
# REPORT workflow
#   ↓
# real memory_agent
#   ↓
# PostgreSQL
#   ↓
# pgvector
#   ↓
# HTTP response
# =========================================================

@pytest.mark.e2e
def test_authenticated_report_e2e(
    test_db,
    monkeypatch
):

    # =====================================================
    # DISABLE EMAIL VERIFICATION
    # =====================================================

    monkeypatch.setattr(
        auth_module,
        "EMAIL_VERIFICATION_ENABLED",
        False
    )

    # =====================================================
    # CREATE REAL TEST USER
    # =====================================================

    postgres_memory = PostgresMemory(
        db=test_db
    )

    auth_service = AuthService(
        postgres_memory=postgres_memory
    )

    identifier = uuid4().hex[:12]

    password = "TestPassword123!"

    user = auth_service.register(
        username=(
            f"e2euser{identifier}"
        ),
        email=(
            f"e2e{identifier}@gmail.com"
        ),
        password=password
    )

    assert user is not None
    assert user.id is not None

    # =====================================================
    # CREATE REAL APPLICATION SESSION
    # =====================================================

    chat_session = DBSession(
        user_id=user.id,
        title="E2E Tesla Analysis",
        ticker="TSLA"
    )

    test_db.add(
        chat_session
    )

    test_db.commit()

    test_db.refresh(
        chat_session
    )

    assert chat_session.id is not None

    # =====================================================
    # DATABASE FACTORY
    #
    # The real memory_agent closes the session it receives.
    #
    # Therefore we create a new SQLAlchemy Session attached
    # to the same pytest transaction instead of passing
    # test_db directly.
    # =====================================================

    def test_db_factory():

        return Session(
            bind=test_db.connection(),
            autoflush=False,
            expire_on_commit=False,
            join_transaction_mode=(
                "create_savepoint"
            )
        )

    # =====================================================
    # REAL MEMORY NODE
    #
    # Real:
    # - memory_agent
    # - PostgresMemory
    # - MemoryManager
    # - VectorMemory
    # - EmbeddingService
    # - PostgreSQL
    # - pgvector
    #
    # Mocked:
    # - Redis
    # =====================================================

    def real_memory_node(state):

        return memory_agent(
            state,
            db_factory=test_db_factory,
            redis_factory=NoOpRedisMemory,
            embedding_factory=EmbeddingService
        )

    # =====================================================
    # DETERMINISTIC REPORT UPSTREAM NODES
    #
    # We don't want Yahoo / external finance providers /
    # Ollama causing ordinary E2E failures.
    # =====================================================

    def fake_intent_node(state):

        assert (
            state["query"]
            == "Analyse Tesla"
        )

        return {
            "intent": Intent.REPORT
        }

    # -----------------------------------------------------

    def fake_asset_node(state):

        return {
            "resolved_asset": {
                "ticker": "TSLA",
                "company_name": "Tesla, Inc."
            }
        }

    # -----------------------------------------------------

    def fake_market_node(state):

        assert (
            state["resolved_asset"][
                "ticker"
            ]
            == "TSLA"
        )

        return {
            "market_analysis": {
                "rsi": 52.0,

                "macd": {
                    "macd": 3.5,
                    "signal": 3.1
                }
            }
        }

    # -----------------------------------------------------

    def fake_fundamentals_node(state):

        assert (
            state["resolved_asset"][
                "ticker"
            ]
            == "TSLA"
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

    def fake_news_node(state):

        assert (
            state["resolved_asset"][
                "ticker"
            ]
            == "TSLA"
        )

        return {
            "news_analysis": [
                {
                    "headline": (
                        "Tesla E2E test news"
                    ),

                    "sentiment": (
                        "positive"
                    )
                }
            ]
        }

    # =====================================================
    # STRATEGY
    #
    # This also verifies the fan-in:
    #
    # market
    # fundamentals
    # news
    #      ↓
    # strategy
    # =====================================================

    def fake_strategy_node(state):

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

    # =====================================================
    # MOCK LLM OUTPUT
    # =====================================================

    expected_report = (
        "Tesla has a strong market "
        "position but carries "
        "valuation risk."
    )

    def fake_report_node(state):

        assert (
            "strategy_analysis"
            in state
        )

        return {
            "llm_report": expected_report
        }

    # =====================================================
    # PROTECT AGAINST WRONG GRAPH BRANCH
    # =====================================================

    def unexpected_node(state):

        raise AssertionError(
            "Unexpected LangGraph branch executed."
        )

    # =====================================================
    # BUILD TEST GRAPH USING REAL PRODUCTION TOPOLOGY
    # =====================================================

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

        # Real persistence
        memory_node=real_memory_node,

        # CHAT must not run
        conversation_memory_node=(
            unexpected_node
        ),

        chat_node=unexpected_node,

        save_chat_node=unexpected_node,

        # RECOMMEND must not run
        recommendation_node=unexpected_node
    )



    monkeypatch.setattr(
        chat_route_module,
        "graph",
        test_graph
    )

    # =====================================================
    # OVERRIDE FASTAPI DATABASE DEPENDENCY
    #
    # This makes HTTP authentication use the pytest DB.
    # =====================================================

    def override_get_db():

        yield test_db

    app.dependency_overrides[
        get_db
    ] = override_get_db

    try:

        # =================================================
        # IMPORTANT FIX
        #
        # Default TestClient host:
        #
        #     testserver
        #
        # TrustedHostMiddleware may reject it with:
        #
        #     400 Bad Request
        #
        # We therefore make the test client use localhost.
        # =================================================

        with TestClient(
            app,
            base_url="http://localhost"
        ) as client:

            # =================================================
            # STEP 1
            # LOGIN THROUGH THE ACTUAL HTTP ENDPOINT
            # =================================================

            login_response = client.post(
                "/auth/login",
                json={
                    "email": user.email,
                    "password": password
                }
            )

            assert (
                login_response.status_code
                == 200
            ), (
                "Login failed.\n"
                f"Status: "
                f"{login_response.status_code}\n"
                f"Response: "
                f"{login_response.text}"
            )

            login_data = (
                login_response.json()
            )

            assert (
                "access_token"
                in login_data
            )

            access_token = (
                login_data["access_token"]
            )

            assert access_token

            # =================================================
            # STEP 2
            # CALL ACTUAL /chat HTTP ENDPOINT
            # =================================================

            response = client.post(
                "/chat",
                json={
                    "message": "Analyse Tesla",
                    "session_id": str(
                        chat_session.id
                    )
                },
                headers={
                    "Authorization": (
                        f"Bearer {access_token}"
                    )
                }
            )

            assert (
                response.status_code
                == 200
            ), (
                "/chat request failed.\n"
                f"Status: "
                f"{response.status_code}\n"
                f"Response: "
                f"{response.text}"
            )
        # =================================================
        # STEP 3
        # VALIDATE HTTP RESPONSE
        # =================================================

        body = response.json()

        assert body is not None

        assert (
                "response"
                in body
        ), (
            "Expected 'response' in /chat response.\n"
            f"Actual response: {body}"
        )

        assert (
                body["response"]
                == expected_report
        )

        assert (
                body["intent"]
                == Intent.REPORT.value
        )
        # =====================================================
        # STEP 4
        # VERIFY REAL ANALYSIS PERSISTENCE
        # =====================================================

        analysis = (
            test_db.query(
                Analysis
            )
            .filter(
                Analysis.session_id
                == chat_session.id
            )
            .order_by(
                Analysis.created_at.desc()
            )
            .first()
        )

        assert (
            analysis is not None
        )

        assert (
            analysis.ticker
            == "TSLA"
        )

        assert (
            analysis.company_name
            == "Tesla, Inc."
        )

        assert (
            analysis.query
            == "Analyse Tesla"
        )

        assert (
            analysis.llm_report
            == expected_report
        )

        # =====================================================
        # STEP 5
        # VERIFY MARKET DATA WAS PERSISTED
        # =====================================================

        assert (
            analysis.market_analysis[
                "rsi"
            ]
            == 52.0
        )

        # =====================================================
        # STEP 6
        # VERIFY FUNDAMENTALS WERE PERSISTED
        # =====================================================

        assert (
            analysis.fundamentals_analysis[
                "sector"
            ]
            == "Consumer Cyclical"
        )

        # =====================================================
        # STEP 7
        # VERIFY NEWS WAS PERSISTED
        # =====================================================

        assert (
            analysis.news_analysis[0][
                "sentiment"
            ]
            == "positive"
        )

        # =====================================================
        # STEP 8
        # VERIFY STRATEGY WAS PERSISTED
        # =====================================================

        assert (
            analysis.strategy_analysis[
                "risks"
            ][0]
            == "High valuation"
        )

        # =====================================================
        # STEP 9
        # VERIFY REAL PGVECTOR RECORD
        # =====================================================

        vector_record = (
            test_db.query(
                AnalysisVector
            )
            .filter(
                AnalysisVector.analysis_id
                == analysis.id
            )
            .first()
        )

        assert (
            vector_record
            is not None
        )

        assert (
            vector_record.analysis_id
            == analysis.id
        )

        assert (
            vector_record.user_id
            == user.id
        )

        assert (
            vector_record.session_id
            == chat_session.id
        )

        assert (
            vector_record.embedded_text
        )

        # =====================================================
        # STEP 10
        # VERIFY BGE EMBEDDING DIMENSION
        #
        # Database column:
        #
        # VECTOR(384)
        # =====================================================

        assert (
            vector_record.embedding
            is not None
        )

        assert (
            len(
                vector_record.embedding
            )
            == 384
        )

    finally:

        # =====================================================
        # ALWAYS REMOVE DEPENDENCY OVERRIDES
        # =====================================================

        app.dependency_overrides.clear()