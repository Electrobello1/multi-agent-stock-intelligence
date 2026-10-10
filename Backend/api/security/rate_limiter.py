from typing import Callable, Optional
from fastapi import Depends
from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from Backend.memory.redis_memory import RedisMemory
from Backend.Resilience.circuit_breaker import CircuitOpenError


redis_memory = RedisMemory()


class RateLimitPolicy:
    """
    Defines a rate-limit policy.
    """

    def __init__(
        self,
        name: str,
        limit: int,
        window_seconds: int
    ):
        if not name:
            raise ValueError(
                "Rate-limit policy name cannot be empty."
            )

        if limit <= 0:
            raise ValueError(
                "Rate-limit limit must be greater than zero."
            )

        if window_seconds <= 0:
            raise ValueError(
                "Rate-limit window must be greater than zero."
            )

        self.name = name
        self.limit = limit
        self.window_seconds = window_seconds


def _get_client_ip(request: Request) -> str:
    """
    Get the client IP.

    We intentionally use request.client.host rather than
    blindly trusting X-Forwarded-For.
    """

    if request.client is None:
        return "unknown"

    return request.client.host or "unknown"


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _increment(
    key: str,
    policy: RateLimitPolicy
) -> None:
    """
    Increment the rate-limit counter and enforce the policy.
    """

    try:
        count = redis_memory.increment_rate_limit(
            key=key,
            ttl=policy.window_seconds
        )

    except CircuitOpenError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Rate-limiting service is temporarily "
                "unavailable. Please try again later."
            ),
            headers={
                "Retry-After": "30"
            }
        ) from e

    except RedisError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Rate-limiting service is temporarily "
                "unavailable. Please try again later."
            ),
            headers={
                "Retry-After": "30"
            }
        ) from e

    if count > policy.limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many requests. "
                "Please try again later."
            ),
            headers={
                "Retry-After": str(
                    policy.window_seconds
                )
            }
        )


def rate_limit_ip(
    policy: RateLimitPolicy
) -> Callable:
    """
    Rate limit requests by client IP.
    """

    async def dependency(
        request: Request
    ) -> None:
        client_ip = _get_client_ip(request)

        key = (
            f"rate_limit:"
            f"{policy.name}:"
            f"ip:{client_ip}"
        )

        _increment(
            key=key,
            policy=policy
        )

    return dependency


def rate_limit_ip_email(
    policy: RateLimitPolicy,
    email_getter: Callable
) -> Callable:
    """
    Rate limit using both client IP and email address.
    """

    async def dependency(
        request: Request
    ) -> None:
        body = await request.json()

        email = email_getter(body)

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required."
            )

        email = _normalize_email(email)
        client_ip = _get_client_ip(request)

        key = (
            f"rate_limit:"
            f"{policy.name}:"
            f"ip:{client_ip}:"
            f"email:{email}"
        )

        _increment(
            key=key,
            policy=policy
        )

    return dependency

def rate_limit_user_ip(
    policy: RateLimitPolicy,
    current_user_dependency: Callable
) -> Callable:

    async def dependency(
        request: Request,
        current_user=Depends(
            current_user_dependency
        )
    ) -> None:
        client_ip = _get_client_ip(request)

        user_id = str(current_user.id)

        key = (
            f"rate_limit:"
            f"{policy.name}:"
            f"user:{user_id}:"
            f"ip:{client_ip}"
        )

        _increment(
            key=key,
            policy=policy
        )

    return dependency

REGISTER_RATE_LIMIT = RateLimitPolicy(
    name="register",
    limit=15,
    window_seconds=3600
)

LOGIN_RATE_LIMIT = RateLimitPolicy(
    name="login",
    limit=5,
    window_seconds=60
)

VERIFY_EMAIL_RATE_LIMIT = RateLimitPolicy(
    name="verify_email",
    limit=5,
    window_seconds=600
)

RESEND_OTP_RATE_LIMIT = RateLimitPolicy(
    name="resend_otp",
    limit=3,
    window_seconds=600
)

REFRESH_TOKEN_RATE_LIMIT = RateLimitPolicy(
    name="refresh_token",
    limit=10,
    window_seconds=60
)

FORGOT_PASSWORD_RATE_LIMIT = RateLimitPolicy(
    name="forgot_password",
    limit=3,
    window_seconds=900
)

RESET_PASSWORD_RATE_LIMIT = RateLimitPolicy(
    name="reset_password",
    limit=5,
    window_seconds=900
)

CHANGE_PASSWORD_RATE_LIMIT = RateLimitPolicy(
    name="change_password",
    limit=5,
    window_seconds=900
)


SESSION_CREATE_RATE_LIMIT = RateLimitPolicy(
    name="session_create",
    limit=10,
    window_seconds=60
)

SESSION_LIST_RATE_LIMIT = RateLimitPolicy(
    name="session_list",
    limit=30,
    window_seconds=60
)

SESSION_GET_RATE_LIMIT = RateLimitPolicy(
    name="session_get",
    limit=60,
    window_seconds=60
)

SESSION_DELETE_RATE_LIMIT = RateLimitPolicy(
    name="session_delete",
    limit=20,
    window_seconds=60
)


CHAT_RATE_LIMIT = RateLimitPolicy(
    name="chat",
    limit=20,
    #limit=200,
    window_seconds=60
)


def get_email_from_body(
    body: dict
) -> Optional[str]:
    return body.get("email")
