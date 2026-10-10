from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
import logging

from Backend.utils.perf_timer import (
    timed_step
)

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from Backend.Routing.intent import Intent
from fastapi.security import OAuth2PasswordRequestForm
from Backend.api.dependencies.Database_connection import get_db
from Backend.api.dependencies.auth import (
    get_auth_service,
    get_current_user
)
from Backend.api.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    VerifyOTPRequest,
    ResendOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,

    MessageResponse,
    CreateSessionRequest,
    SessionListResponse,
    SessionResponse,
    ChatRequest,
    ChatResponse
)
from Backend.api.security.rate_limiter import (
    rate_limit_ip,
    rate_limit_user_ip,
    rate_limit_ip_email,
    REGISTER_RATE_LIMIT,
    LOGIN_RATE_LIMIT,
    VERIFY_EMAIL_RATE_LIMIT,
    RESEND_OTP_RATE_LIMIT,
    REFRESH_TOKEN_RATE_LIMIT,
    FORGOT_PASSWORD_RATE_LIMIT,
    RESET_PASSWORD_RATE_LIMIT,
    CHANGE_PASSWORD_RATE_LIMIT,
    SESSION_CREATE_RATE_LIMIT,
    SESSION_LIST_RATE_LIMIT,
    SESSION_GET_RATE_LIMIT,
    SESSION_DELETE_RATE_LIMIT,
    CHAT_RATE_LIMIT,
    get_email_from_body
)
from Backend.services.auth_service import AuthService

from Backend.graph.Graph import graph
from Backend.memory.postgres_memory import PostgresMemory

from contextlib import asynccontextmanager
from fastapi import FastAPI

from Backend.database.connection import Base, engine
# Import models so they are registered
from Backend.database.user_table import User
from Backend.database.sessions_table import Session
from Backend.database.analysis import Analysis
from Backend.database.Analysis_vector import AnalysisVector
from Backend.database.email_verification import EmailVerification
from Backend.database.password_reset import PasswordResetToken

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield



# ============================================================
# Authentication Routes
# ============================================================



auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@auth_router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            rate_limit_ip(
                REGISTER_RATE_LIMIT
            )
        )
    ]
)
def register(
    request: RegisterRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        auth_service.register(
            username=request.username,
            email=request.email,
            password=request.password
        )

        return {
            "message": "Registration successful."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# login  endpoint for swagger UI
@auth_router.post(
    "/token",
    response_model=TokenResponse,
    dependencies=[
        Depends(
            rate_limit_ip(
                LOGIN_RATE_LIMIT
            )
        )
    ]
)
def oauth2_token(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        return auth_service.login(
            email=form_data.username,
            password=form_data.password
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )
@auth_router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[
        Depends(
            rate_limit_ip(
                LOGIN_RATE_LIMIT
            )
        )
    ]
)
def login(
    request: LoginRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        return auth_service.login(
            email=request.email,
            password=request.password
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[
        Depends(
            rate_limit_ip(
                REFRESH_TOKEN_RATE_LIMIT
            )
        )
    ]
)
def refresh_token(
    request: RefreshTokenRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        return auth_service.refresh_access_token(
            request.refresh_token
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@auth_router.post(
    "/verify-email",
    response_model=MessageResponse,
    dependencies=[
        Depends(
            rate_limit_ip_email(
                VERIFY_EMAIL_RATE_LIMIT,
                get_email_from_body
            )
        )
    ]
)
def verify_email(
    request: VerifyOTPRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        auth_service.verify_email(
            email=request.email,
            otp=request.otp
        )

        return {
            "message": "Email verified successfully."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@auth_router.post(
    "/resend-otp",
    response_model=MessageResponse,
    dependencies=[
        Depends(
            rate_limit_ip_email(
                RESEND_OTP_RATE_LIMIT,
                get_email_from_body
            )
        )
    ]
)
def resend_otp(
    request: ResendOTPRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        auth_service.resend_verification_otp(
            email=request.email
        )

        return {
            "message": "Verification code sent."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@auth_router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[
        Depends(
            rate_limit_ip_email(
                FORGOT_PASSWORD_RATE_LIMIT,
                get_email_from_body
            )
        )
    ]
)
def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        auth_service.forgot_password(
            email=request.email
        )

        return {
            "message": "Password reset instructions sent."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@auth_router.post(
    "/reset-password",
    response_model=MessageResponse,
    dependencies=[
        Depends(
            rate_limit_ip(
                RESET_PASSWORD_RATE_LIMIT
            )
        )
    ]
)
def reset_password(
    request: ResetPasswordRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ]
):
    try:
        auth_service.reset_password(
            token=request.token,
            new_password=request.new_password
        )

        return {
            "message": "Password reset successfully."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@auth_router.post(
    "/change-password",
    response_model=MessageResponse,
    dependencies=[
        Depends(
            rate_limit_user_ip(
                CHANGE_PASSWORD_RATE_LIMIT,
                get_current_user
            )
        )
    ]
)
def change_password(
    request: ChangePasswordRequest,
    auth_service: Annotated[
        AuthService,
        Depends(get_auth_service)
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
):
    try:
        auth_service.change_password(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )

        return {
            "message": "Password changed successfully."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================
# Session Routes
# ============================================================

session_router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


def get_postgres_memory(
    db: Annotated[
        Session,
        Depends(get_db)
    ]
) -> PostgresMemory:
    return PostgresMemory(db)


def _serialize_session(
    session
) -> SessionResponse:
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        ticker=session.ticker,
        is_deleted=session.is_deleted
    )


@session_router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            rate_limit_user_ip(
                SESSION_CREATE_RATE_LIMIT,
                get_current_user
            )
        )
    ]
)
def create_session(
    request: CreateSessionRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],
    postgres_memory: Annotated[
        PostgresMemory,
        Depends(get_postgres_memory)
    ]
):
    try:
        session = postgres_memory.create_session(
            user_id=current_user.id,
            title=request.title,
            ticker=request.ticker
        )

        return _serialize_session(session)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@session_router.get(
    "",
    response_model=SessionListResponse,
    dependencies=[
        Depends(
            rate_limit_user_ip(
                SESSION_LIST_RATE_LIMIT,
                get_current_user
            )
        )
    ]
)
def get_sessions(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],
    postgres_memory: Annotated[
        PostgresMemory,
        Depends(get_postgres_memory)
    ],
    page: int = Query(
        default=1,
        ge=1
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100
    )
):
    try:
        sessions = postgres_memory.get_user_sessions(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        return SessionListResponse(
            sessions=[
                _serialize_session(session)
                for session in sessions
            ],
            page=page,
            page_size=page_size
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@session_router.get(
    "/{session_id}",
    response_model=SessionResponse,
    dependencies=[
        Depends(
            rate_limit_user_ip(
                SESSION_GET_RATE_LIMIT,
                get_current_user
            )
        )
    ]
)
def get_session(
    session_id: str,
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],
    postgres_memory: Annotated[
        PostgresMemory,
        Depends(get_postgres_memory)
    ]
):
    try:
        session = postgres_memory.get_session(
            session_id=session_id,
            user_id=current_user.id
        )

        return _serialize_session(session)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@session_router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            rate_limit_user_ip(
                SESSION_DELETE_RATE_LIMIT,
                get_current_user
            )
        )
    ]
)
def delete_session(
    session_id: str,
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],
    postgres_memory: Annotated[
        PostgresMemory,
        Depends(get_postgres_memory)
    ]
):
    try:
        postgres_memory.soft_delete_session(
            session_id=session_id,
            user_id=current_user.id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


    # ============================================================
    # Chat Routes
    # ============================================================



chat_router = APIRouter(
        prefix="/chat",
        tags=["Chat"]
    )


@chat_router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            rate_limit_user_ip(
                CHAT_RATE_LIMIT,
                get_current_user
            )
        )
    ]
)
def chat(
    request: ChatRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],
    postgres_memory: Annotated[
        PostgresMemory,
        Depends(get_postgres_memory)
    ]
):
    try:
        # ----------------------------------------------------
        # Validate message
        # ----------------------------------------------------

        message = request.message.strip()

        if not message:
            raise ValueError(
                "Message cannot be empty."
            )

        # ----------------------------------------------------
        # Verify session ownership
        # ----------------------------------------------------

        session = postgres_memory.get_session(
            session_id=request.session_id,
            user_id=current_user.id
        )

        # ----------------------------------------------------
        # Build initial LangGraph state
        # ----------------------------------------------------

        initial_state = {
            "query": message,
            "user_id": str(current_user.id),
            "session_id": str(session.id)
        }

        # ----------------------------------------------------
        # Execute LangGraph
        # ----------------------------------------------------

        with timed_step(
                logger,
                "graph_total",
                user_id=str(
                    current_user.id
                ),
                session_id=str(
                    request.session_id
                ),
        ):
            result = graph.invoke(
                initial_state
            )

        # ----------------------------------------------------
        # Get intent returned by LangGraph
        # ----------------------------------------------------

        raw_intent = result.get(
            "intent"
        )

        if raw_intent is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "LangGraph did not return an intent."
                )
            )

        # ----------------------------------------------------
        # Normalize intent
        # ----------------------------------------------------

        if isinstance(
            raw_intent,
            Intent
        ):
            intent = raw_intent

        else:
            try:
                intent = Intent(
                    raw_intent
                )

            except (
                ValueError,
                TypeError
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "LangGraph returned an unsupported "
                        f"intent: {raw_intent!r}"
                    )
                )

        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        if intent == Intent.CHAT:

            response = result.get(
                "chat_response"
            )

            if not response:
                raise HTTPException(
                    status_code=(
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "Chat workflow completed without "
                        "a chat response."
                    )
                )

            return ChatResponse(
                session_id=str(
                    session.id
                ),
                intent=intent.value,
                response=response
            )

        # ----------------------------------------------------
        # REPORT
        # ----------------------------------------------------

        if intent == Intent.REPORT:

            response = result.get(
                "llm_report"
            )

            if not response:
                raise HTTPException(
                    status_code=(
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "Report workflow completed without "
                        "an LLM report."
                    )
                )

            return ChatResponse(
                session_id=str(
                    session.id
                ),
                intent=intent.value,
                response=response
            )

        # ----------------------------------------------------
        # RECOMMEND
        # ----------------------------------------------------

        if intent == Intent.RECOMMEND:

            candidates = result.get(
                "recommendation_candidates"
            )

            if candidates is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "Recommendation workflow completed "
                        "without candidates."
                    )
                )

            return ChatResponse(
                session_id=str(
                    session.id
                ),
                intent=intent.value,
                recommendation_candidates=candidates
            )

        # ----------------------------------------------------
        # Defensive fallback
        # ----------------------------------------------------

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "LangGraph returned an unsupported "
                f"intent: {intent!r}"
            )
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



