import logging

from Backend.memory.postgres_memory import PostgresMemory
from Backend.memory.redis_memory import RedisMemory
from Backend.memory.vector_memory import VectorMemory

logger = logging.getLogger(__name__)


class MemoryManager:

    def __init__(

            self,

            postgres_memory: PostgresMemory,

            redis_memory: RedisMemory,

            vector_memory: VectorMemory

    ):

        self.postgres = postgres_memory

        self.redis = redis_memory

        self.vector = vector_memory

    # ============================================================
    # Internal Helpers
    # ============================================================

    @staticmethod
    def _analysis_to_cache_dict(analysis):
        """
        Convert an Analysis ORM object into a
        JSON-serializable dictionary for Redis.
        """

        return {

            "id": str(analysis.id),

            "session_id": str(analysis.session_id),

            "ticker": analysis.ticker,
            "company_name": analysis.company_name,
            "query":analysis.query,

            "market_analysis": analysis.market_analysis,

            "fundamentals_analysis": analysis.fundamentals_analysis,

            "news_analysis": analysis.news_analysis,

            "strategy_analysis": analysis.strategy_analysis,

            "llm_report": analysis.llm_report,

            "created_at": analysis.created_at.isoformat()

        }

    # ============================================================
    # Analysis
    # ============================================================

    def save_analysis(

            self,

            session_id,

            user_id,

            analysis_data

    ):
        """
        Save an analysis to PostgreSQL,
        cache it in Redis,
        and store its embedding.
        """

        analysis = self.postgres.save_analysis(

            session_id=session_id,

            user_id=user_id,

            analysis_data=analysis_data

        )

        self.redis.cache_analysis(

            session_id=session_id,

            analysis_id=analysis.id,

            analysis=self._analysis_to_cache_dict(

                analysis

            )

        )

        self.vector.upsert_vector(

            analysis_id=analysis.id,

            session_id=session_id,

            user_id=user_id,

            embedded_text=analysis.llm_report

        )

        return analysis

    def get_analysis(

            self,

            analysis_id,

            session_id,

            user_id

    ):
        """
        Cache-aside retrieval.
        """

        cached = self.redis.get_cached_analysis(

            session_id=session_id,

            analysis_id=analysis_id

        )

        if cached is not None:

            return cached

        analysis = self.postgres.get_analysis(

            analysis_id=analysis_id,

            user_id=user_id

        )

        cache_data = self._analysis_to_cache_dict(

            analysis

        )

        self.redis.cache_analysis(

            session_id=session_id,

            analysis_id=analysis.id,

            analysis=cache_data

        )

        return cache_data

    def delete_analysis(

            self,

            analysis_id,

            session_id,

            user_id

    ):
        """
        Permanently delete an analysis.
        """

        self.postgres.delete_analysis(

            analysis_id=analysis_id,

            user_id=user_id

        )

        self.redis.delete_analysis(

            session_id=session_id,

            analysis_id=analysis_id

        )

        self.vector.delete_vector(

            analysis_id=analysis_id

        )

        return True

    # ============================================================
    # Semantic Retrieval (RAG)
    # ============================================================

    def retrieve_context(

            self,

            user_id,

            query,

            session_id=None,

            top_k=5

    ):

        return self.vector.search_similar(

            user_id=user_id,

            query=query,

            session_id=session_id,

            top_k=top_k

        )

    # ============================================================
    # Redis
    # ============================================================

    def clear_session_cache(

            self,

            session_id

    ):

        self.redis.clear_session_cache(

            session_id

        )

        return True

    # ============================================================
    # Sessions
    # ============================================================

    def create_session(

            self,

            user_id,

            title=None

    ):

        return self.postgres.create_session(

            user_id=user_id,

            title=title

        )

    def get_session(

            self,

            session_id,

            user_id

    ):

        return self.postgres.get_session(

            session_id=session_id,

            user_id=user_id

        )

    def delete_session(

            self,

            session_id,

            user_id

    ):
        """
        Soft delete a chat session.
        """

        self.postgres.soft_delete_session(

            session_id=session_id,

            user_id=user_id

        )

        self.redis.clear_session_cache(

            session_id

        )

        return True

    def restore_session(

            self,

            session_id,

            user_id

    ):

        return self.postgres.restore_session(

            session_id=session_id,

            user_id=user_id

        )