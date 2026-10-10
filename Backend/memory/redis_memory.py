import json
import logging
import os

from redis import Redis
from redis.exceptions import RedisError

from dotenv import load_dotenv

from Backend.Resilience.breakers import redis_breaker


load_dotenv()

logger = logging.getLogger(__name__)


class RedisMemory:

    DEFAULT_TTL = 3600

    def __init__(
        self,
        redis_url=None
    ):
        redis_url = (
            redis_url
            or os.getenv("REDIS_URL")
        )

        if not redis_url:
            raise RuntimeError(
                "REDIS_URL environment variable is not configured."
            )

        self.redis = Redis.from_url(
            redis_url,
            decode_responses=True
        )

    # ======================================
    # Internal Helpers
    # ======================================

    def _make_key(
        self,
        namespace,
        key
    ):
        return f"{namespace}:{key}"

    # ======================================
    # Generic Cache Methods
    # ======================================

    def set(
        self,
        namespace,
        key,
        value,
        ttl=None
    ):
        try:
            redis_key = self._make_key(
                namespace,
                key
            )

            redis_breaker.call(
                self.redis.set,
                redis_key,
                json.dumps(value),
                ex=ttl or self.DEFAULT_TTL
            )

            return True

        except RedisError as e:
            logger.exception(
                "Redis SET failed: %s",
                e
            )

            # Redis is a cache, so failure should
            # not normally break the application.
            return False

    def get(
        self,
        namespace,
        key
    ):
        try:
            redis_key = self._make_key(
                namespace,
                key
            )

            value = redis_breaker.call(
                self.redis.get,
                redis_key
            )

            if value is None:
                return None

            return json.loads(value)

        except RedisError as e:
            logger.exception(
                "Redis GET failed: %s",
                e
            )

            # Cache miss behavior.
            return None

    def delete(
        self,
        namespace,
        key
    ):
        try:
            redis_key = self._make_key(
                namespace,
                key
            )

            redis_breaker.call(
                self.redis.delete,
                redis_key
            )

            return True

        except RedisError as e:
            logger.exception(
                "Redis DELETE failed: %s",
                e
            )

            return False

    def exists(
        self,
        namespace,
        key
    ):
        try:
            redis_key = self._make_key(
                namespace,
                key
            )

            return bool(
                redis_breaker.call(
                    self.redis.exists,
                    redis_key
                )
            )

        except RedisError as e:
            logger.exception(
                "Redis EXISTS failed: %s",
                e
            )

            return False

    # ======================================
    # Market Cache
    # ======================================

    def cache_market_data(
        self,
        ticker,
        data,
        ttl=3600
    ):
        return self.set(
            "market",
            ticker,
            data,
            ttl
        )

    def get_market_data(
        self,
        ticker
    ):
        return self.get(
            "market",
            ticker
        )

    # ======================================
    # Fundamentals Cache
    # ======================================

    def cache_fundamentals(
        self,
        ticker,
        data,
        ttl=86400
    ):
        return self.set(
            "fundamentals",
            ticker,
            data,
            ttl
        )

    def get_fundamentals(
        self,
        ticker
    ):
        return self.get(
            "fundamentals",
            ticker
        )

    # ======================================
    # News Cache
    # ======================================

    def cache_news(
        self,
        ticker,
        data,
        ttl=1800
    ):
        return self.set(
            "news",
            ticker,
            data,
            ttl
        )

    def get_news(
        self,
        ticker
    ):
        return self.get(
            "news",
            ticker
        )

    # ======================================
    # Analysis Cache
    # ======================================

    def cache_analysis(
        self,
        session_id,
        analysis_id,
        analysis,
        ttl=3600
    ):
        key = (
            f"{session_id}:{analysis_id}"
        )

        return self.set(
            "analysis",
            key,
            analysis,
            ttl
        )

    def get_cached_analysis(
        self,
        session_id,
        analysis_id
    ):
        key = (
            f"{session_id}:{analysis_id}"
        )

        return self.get(
            "analysis",
            key
        )

    def delete_analysis(
        self,
        session_id,
        analysis_id
    ):
        key = (
            f"{session_id}:{analysis_id}"
        )

        return self.delete(
            "analysis",
            key
        )

    def cache_exists(
        self,
        session_id,
        analysis_id
    ):
        key = (
            f"{session_id}:{analysis_id}"
        )

        return self.exists(
            "analysis",
            key
        )

    def clear_session_cache(
        self,
        session_id
    ):
        pattern = (
            f"analysis:{session_id}:*"
        )

        return self.clear_pattern(
            pattern
        )

    # ======================================
    # Utilities
    # ======================================

    def increment_rate_limit(
            self,
            key,
            ttl
    ):
        try:
            count = redis_breaker.call(
                self.redis.incr,
                key
            )

            if count == 1:
                redis_breaker.call(
                    self.redis.expire,
                    key,
                    ttl
                )

            return count

        except RedisError as e:
            logger.exception(
                "Redis rate limit operation failed: %s",
                e
            )

            raise

    def clear_pattern(
        self,
        pattern
    ):
        """
        Delete keys matching a pattern.

        SCAN is used instead of KEYS so that Redis
        is not blocked by a potentially expensive
        keyspace scan.
        """

        try:
            keys = []

            for key in redis_breaker.call(
                self.redis.scan_iter,
                match=pattern
            ):
                keys.append(key)

            if keys:
                redis_breaker.call(
                    self.redis.delete,
                    *keys
                )

            return True

        except RedisError as e:
            logger.exception(
                "Redis pattern deletion failed: %s",
                e
            )

            return False