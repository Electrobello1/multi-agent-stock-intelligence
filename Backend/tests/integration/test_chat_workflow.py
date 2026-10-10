import pytest

from uuid import uuid4
from sqlalchemy.orm import Session

import Backend.services.auth_service as auth_module

from Backend.Routing.intent import Intent
from Backend.memory.postgres_memory import PostgresMemory
from Backend.database.sessions_table import (
    Session as DBSession
)

from Backend.embeddings.embedding_service import (
    EmbeddingService
)

from Backend.services.context_builder import (
    ContextBuilder
)

from Backend.Agents.memory_agent import (
    memory_agent
)

from Backend.Agents.conversation_agent import (
    conversation_memory_agent,
    save_chat_response_agent
)

# Adjust only if your graph module has another name.
from Backend.graph.Graph import build_graph


# ---------------------------------------------------------
# Redis stub
# ---------------------------------------------------------

class NoOpRedisMemory:

    def __getattr__(self, name):

        def no_op(*args, **kwargs):
            return None

        return no_op


# ---------------------------------------------------------
# Test user and session
# ---------------------------------------------------------

@pytest.fixture
def chat_test_context(
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
        username=f"chatuser{identifier}",
        email=f"chat{identifier}@gmail.com",
        password="TestPassword123!"
    )

    session = DBSession(
        user_id=user.id,
        title="Chat Memory Integration Test",
        ticker="TSLA"
    )

    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)

    return {
        "user": user,
        "session": session
    }


@pytest.mark.integration
def test_complete_chat_memory_workflow(
    test_db,
    chat_test_context
):

    user = chat_test_context[
        "user"
    ]

    chat_session = chat_test_context[
        "session"
    ]

    # -----------------------------------------------------
    # Factory using pytest's database transaction
    # -----------------------------------------------------

    def test_db_factory():

        return Session(
            bind=test_db.connection(),
            autoflush=False,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint"
        )

    # -----------------------------------------------------
    # First seed the database with a real analysis
    # and a real pgvector embedding.
    # -----------------------------------------------------

    seed_state = {
        "query": "Analyse Tesla",

        "user_id": str(
            user.id
        ),

        "session_id": str(
            chat_session.id
        ),

        "resolved_asset": {
            "ticker": "TSLA",
            "company_name": "Tesla, Inc."
        },

        "market_analysis": {
            "rsi": 51.5,

            "macd": {
                "macd": 4.1,
                "signal": 3.7
            }
        },

        "fundamentals_analysis": {
            "sector": "Consumer Cyclical",
            "pe_ratio": 50.0
        },

        "news_analysis": [
            {
                "headline": (
                    "Tesla test headline"
                ),
                "sentiment": "positive"
            }
        ],

        "strategy_analysis": {
            "strengths": [
                "Strong brand"
            ],

            "risks": [
                "High valuation",
                "Competitive pressure"
            ]
        },

        "llm_report": (
            "Tesla has a strong brand, "
            "but major risks include high "
            "valuation and competitive pressure."
        )
    }

    seed_result = memory_agent(
        seed_state,
        db_factory=test_db_factory,
        redis_factory=NoOpRedisMemory,
        embedding_factory=EmbeddingService
    )

    assert (
        seed_result.get("analysis_id")
        is not None
    )

    # -----------------------------------------------------
    # Real conversation-memory node
    # -----------------------------------------------------

    def real_conversation_memory(
        state
    ):

        return conversation_memory_agent(
            state,
            db_factory=test_db_factory,
            redis_factory=NoOpRedisMemory,
            embedding_factory=EmbeddingService,
            context_builder_factory=ContextBuilder
        )

    # -----------------------------------------------------
    # Mock ONLY the chat LLM
    # -----------------------------------------------------

    def fake_chat_llm(state):

        assert (
            "conversation_history"
            in state
        )

        assert (
            "latest_analysis"
            in state
        )

        assert (
            state["latest_analysis"]
            is not None
        )

        assert (
            "retrieved_context"
            in state
        )

        return {
            "chat_response": (
                "The main risks previously identified "
                "were high valuation and "
                "competitive pressure."
            )
        }

    # -----------------------------------------------------
    # Real assistant-message persistence
    # -----------------------------------------------------

    def real_save_chat_response(
        state
    ):

        return save_chat_response_agent(
            state,
            db_factory=test_db_factory
        )

    # -----------------------------------------------------
    # Intent
    # -----------------------------------------------------

    def fake_intent_node(state):

        return {
            "intent": Intent.CHAT
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

        conversation_memory_node=(
            real_conversation_memory
        ),

        chat_node=fake_chat_llm,

        save_chat_node=(
            real_save_chat_response
        ),

        asset_node=unexpected_node,
        market_node=unexpected_node,
        fundamentals_node=unexpected_node,
        news_node=unexpected_node,
        strategy_node=unexpected_node,
        report_node=unexpected_node,
        memory_node=unexpected_node,
        recommendation_node=unexpected_node,
    )

    # -----------------------------------------------------
    # Execute conversational follow-up
    # -----------------------------------------------------

    query = (
        "What are the main risks "
        "you identified?"
    )

    result = test_graph.invoke(
        {
            "query": query,
            "user_id": str(
                user.id
            ),
            "session_id": str(
                chat_session.id
            )
        }
    )

    # -----------------------------------------------------
    # Graph result
    # -----------------------------------------------------

    assert (
        result["intent"]
        == Intent.CHAT
    )

    assert (
        result["chat_response"]
        == (
            "The main risks previously identified "
            "were high valuation and "
            "competitive pressure."
        )
    )

    assert (
        result["latest_analysis"]
        is not None
    )

    assert (
        result[
            "latest_analysis"
        ]["llm_report"]
        == (
            "Tesla has a strong brand, "
            "but major risks include high "
            "valuation and competitive pressure."
        )
    )

    assert (
        "conversation_history"
        in result
    )

    assert (
        "retrieved_context"
        in result
    )

    # -----------------------------------------------------
    # Verify REAL PostgreSQL message persistence
    # -----------------------------------------------------

    memory = PostgresMemory(
        db=test_db
    )

    history = (
        memory.get_chat_history(
            session_id=chat_session.id,
            user_id=user.id
        )
    )

    assert len(history) >= 2

    roles = [
        message.role
        for message in history
    ]

    assert "user" in roles
    assert "assistant" in roles

    user_messages = [
        message.content
        for message in history
        if message.role == "user"
    ]

    assistant_messages = [
        message.content
        for message in history
        if message.role == "assistant"
    ]

    assert query in user_messages

    assert (
        "The main risks previously identified "
        "were high valuation and "
        "competitive pressure."
        in assistant_messages
    )