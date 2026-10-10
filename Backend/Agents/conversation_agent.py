
import logging

from Backend.database.connection import SessionLocal
from Backend.memory.postgres_memory import PostgresMemory
from Backend.memory.redis_memory import RedisMemory
from Backend.memory.vector_memory import VectorMemory
from Backend.memory.memory_manager import MemoryManager

from Backend.services.context_builder import ContextBuilder
from Backend.utils.perf_timer import (
    timed_step
)

from Backend.embeddings.embedding_provider import (
    get_embedding_service
)

logger = logging.getLogger(__name__)


RECENT_MESSAGE_LIMIT = 20
RAG_TOP_K = 5


# ---------------------------------------------------------
# Reusable application services
# ---------------------------------------------------------

redis_memory = RedisMemory,
embedding_factory=get_embedding_service,
context_builder = ContextBuilder,
def conversation_memory_agent(
    state,
    db_factory=SessionLocal,
    redis_factory=RedisMemory,
    embedding_factory=get_embedding_service,
    context_builder_factory=ContextBuilder,
):
    """
    Prepare all memory and context required by the chat LLM.
    """

    user_id = state.get("user_id")
    session_id = state.get("session_id")
    query = state.get("query")

    if user_id is None:
        raise ValueError(
            "conversation_memory_agent requires 'user_id'."
        )

    if session_id is None:
        raise ValueError(
            "conversation_memory_agent requires 'session_id'."
        )

    if query is None:
        raise ValueError(
            "conversation_memory_agent requires 'query'."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "conversation_memory_agent requires a non-empty query."
        )

    db = db_factory()

    try:
        postgres_memory = PostgresMemory(
            db=db
        )

        redis_memory = redis_factory()

        embedding_service = embedding_factory()

        vector_memory = VectorMemory(
            db=db,
            embedding_service=embedding_service
        )

        memory_manager = MemoryManager(
            postgres_memory=postgres_memory,
            redis_memory=redis_memory,
            vector_memory=vector_memory
        )

        context_builder = context_builder_factory()

        # ---------------------------------------------
        # Save user message
        # ---------------------------------------------

        with timed_step(
            logger,
            "save_user_message",
            user_id=user_id,
            session_id=session_id,
        ):
            postgres_memory.save_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=query
            )

        # ---------------------------------------------
        # Recent conversation history
        # ---------------------------------------------

        with timed_step(
            logger,
            "get_chat_history",
            user_id=user_id,
            session_id=session_id,
        ):
            history = postgres_memory.get_chat_history(
                session_id=session_id,
                user_id=user_id
            )

        recent_history = history[
            -RECENT_MESSAGE_LIMIT:
        ]

        conversation_history = [
            {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at
            }
            for message in recent_history
        ]

        # ---------------------------------------------
        # Latest analysis
        # ---------------------------------------------

        with timed_step(
            logger,
            "get_latest_analysis",
            user_id=user_id,
            session_id=session_id,
        ):
            latest_analysis_record = (
                postgres_memory.get_latest_analysis(
                    session_id=session_id,
                    user_id=user_id
                )
            )

        if latest_analysis_record is not None:

            latest_analysis = {
                "id": str(
                    latest_analysis_record.id
                ),
                "llm_report": (
                    latest_analysis_record.llm_report
                ),
                "created_at": (
                    latest_analysis_record.created_at
                )
            }

        else:
            latest_analysis = None

        # ---------------------------------------------
        # Vector / RAG context
        # ---------------------------------------------

        with timed_step(
            logger,
            "retrieve_context",
            user_id=user_id,
            session_id=session_id,
        ):
            contexts = memory_manager.retrieve_context(
                user_id=user_id,
                query=query,
                session_id=session_id,
                top_k=RAG_TOP_K
            )

        # ---------------------------------------------
        # Build context
        # ---------------------------------------------

        with timed_step(
            logger,
            "build_context",
            user_id=user_id,
            session_id=session_id,
        ):
            retrieved_context = context_builder.build(
                contexts
            )

        # ---------------------------------------------
        # Partial LangGraph update only
        # ---------------------------------------------

        return {
            "conversation_history": conversation_history,
            "latest_analysis": latest_analysis,
            "retrieved_context": retrieved_context,
        }

    except Exception:
        logger.exception(
            "Failed to prepare conversation memory "
            "for user=%s session=%s",
            user_id,
            session_id
        )
        raise

    finally:
        db.close()
def save_chat_response_agent(
        state,
        db_factory=SessionLocal
):
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    response = state.get("chat_response")

    if user_id is None:
        raise ValueError(
            "save_chat_response_agent requires 'user_id'."
        )

    if session_id is None:
        raise ValueError(
            "save_chat_response_agent requires 'session_id'."
        )

    if response is None:
        raise ValueError(
            "save_chat_response_agent requires "
            "'chat_response' in state."
        )

    response = response.strip()

    if not response:
        raise ValueError(
            "save_chat_response_agent received "
            "an empty chat response."
        )

    db = db_factory()

    try:
        postgres_memory = PostgresMemory(
            db=db
        )

        with timed_step(
                logger,
                "save_assistant_message",
                user_id=user_id,
                session_id=session_id,
        ):

         postgres_memory.save_message(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=response
          )

        return {}

    except Exception:
        logger.exception(
            "Failed to save assistant chat response "
            "for user=%s session=%s",
            user_id,
            session_id
        )
        raise

    finally:
        db.close()