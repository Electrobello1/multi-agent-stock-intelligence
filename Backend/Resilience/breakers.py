from Backend.Resilience.circuit_breaker import (
    CircuitBreaker,
)



yahoo_market_breaker = CircuitBreaker(
    name="yahoo_market",
    failure_threshold=5,
    recovery_timeout=30
)

polygon_market_breaker = CircuitBreaker(
    name="polygon_market",
    failure_threshold=5,
    recovery_timeout=30
)

alphavantage_market_breaker = CircuitBreaker(
    name="alphavantage_market",
    failure_threshold=5,
    recovery_timeout=30
)
yahoo_fundamental_breaker = CircuitBreaker(
    name="yahoo_fundamentals",
    failure_threshold=5,
    recovery_timeout=30,
)

alphavantage_fundamental_breaker = CircuitBreaker(
    name="alphavantage_fundamentals",
    failure_threshold=5,
    recovery_timeout=30,
)

news_breaker = CircuitBreaker(
    name="news_api",
    failure_threshold=5,
    recovery_timeout=30,
)

candidate_breaker = CircuitBreaker(
    name="candidate_provider",
    failure_threshold=5,
    recovery_timeout=30,
)

llm_breaker = CircuitBreaker(
    name="llm",
    failure_threshold=3,
    recovery_timeout=30,
)

postgres_breaker = CircuitBreaker(
    name="postgres",
    failure_threshold=5,
    recovery_timeout=15,
)

redis_breaker = CircuitBreaker(
    name="redis",
    failure_threshold=5,
    recovery_timeout=15,
)

vector_breaker = CircuitBreaker(
    name="vector",
    failure_threshold=5,
    recovery_timeout=15,
)

embedding_breaker = CircuitBreaker(
    name="embedding",
    failure_threshold=3,
    recovery_timeout=30,
)