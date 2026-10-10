import logging

from Backend.database.connection import SessionLocal

from Backend.memory.postgres_memory import PostgresMemory
from Backend.memory.redis_memory import RedisMemory
from Backend.memory.vector_memory import VectorMemory
from Backend.memory.memory_manager import MemoryManager

from Backend.embeddings.embedding_provider import (
    get_embedding_service
)


logger = logging.getLogger(__name__)

def memory_agent(
    state,
    db_factory=SessionLocal,
    redis_factory=RedisMemory,
    embedding_factory=get_embedding_service(),
):

    user_id = state.get("user_id")
    session_id = state.get("session_id")

    if user_id is None:
        raise ValueError(
            "memory_agent requires 'user_id' in StockState."
        )

    if session_id is None:
        raise ValueError(
            "memory_agent requires 'session_id' in StockState."
        )

    resolved_asset = state.get(
        "resolved_asset",
        {}
    )

    analysis_data = {
        "query": state.get("query"),

        "ticker": (
            resolved_asset.get("ticker")
            or resolved_asset.get("symbol")
        ),

        "company_name": (
            resolved_asset.get("company_name")
            or resolved_asset.get("name")
        ),

        "market_analysis": state.get(
            "market_analysis",
            {}
        ),

        "fundamentals_analysis": state.get(
            "fundamentals_analysis",
            {}
        ),

        "news_analysis": state.get(
            "news_analysis",
            []
        ),

        "strategy_analysis": state.get(
            "strategy_analysis",
            {}
        ),

        "llm_report": state.get(
            "llm_report"
        )
    }

    db = db_factory()

    try:
        postgres_memory = PostgresMemory(
            db=db
        )

        redis_memory = redis_factory()

        embedding_service = (
            embedding_factory()
        )

        vector_memory = VectorMemory(
            db=db,
            embedding_service=embedding_service
        )

        memory_manager = MemoryManager(
            postgres_memory=postgres_memory,
            redis_memory=redis_memory,
            vector_memory=vector_memory
        )

        analysis = (
            memory_manager.save_analysis(
                session_id=session_id,
                user_id=user_id,
                analysis_data=analysis_data
            )
        )

        return {
            "analysis_id": analysis.id
        }

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to persist completed "
            "stock analysis."
        )

        raise

    finally:
        db.close()