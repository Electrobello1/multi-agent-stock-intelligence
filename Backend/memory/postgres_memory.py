from __future__ import annotations

import logging
from fastapi.encoders import jsonable_encoder
from contextlib import contextmanager

from Backend.exceptions import *
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from Backend.database.sessions_table import (
    Session as ChatSession
)
from Backend.database.email_verification import (
    EmailVerification
)
from Backend.database.messages import (
    Message
)

from Backend.database.analysis import (
    Analysis
)

from Backend.database.user_table import User

from Backend.Resilience.breakers import (
    postgres_breaker
)

from Backend.database.password_reset import (
    PasswordResetToken,
)

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    filename="logs/app.log"
)


class MemoryError(Exception):
    pass


class SessionNotFoundError(MemoryError):
    pass


class AnalysisNotFoundError(MemoryError):
    pass


class PostgresMemory:

    def __init__(
        self,
        db: Session
    ):
        self.db = db

    # ============================================================
    # Database Circuit Breaker Helpers
    # ============================================================
    def _execute_db(self, operation, *args, **kwargs):
        return postgres_breaker.call(
            operation,
            *args,
            **kwargs
        )

    def _flush(self):
        """
        Execute SQLAlchemy flush through the circuit breaker.
        """

        return self._execute_db(
            self.db.flush
        )

    def _commit(self):
        """
        Execute SQLAlchemy commit through the circuit breaker.
        """

        return self._execute_db(
            self.db.commit
        )

    def _refresh_model(self, model):
        self._execute_db(
            self.db.refresh,
            model
        )

        return model
    # ============================================================
    # Transaction
    # ============================================================

    @contextmanager
    def transaction(self):

        try:

            yield

            self._commit()

        except SQLAlchemyError as e:

            self.db.rollback()

            logger.exception(e)

            raise

        except Exception:

            self.db.rollback()

            logger.exception(
                "Unexpected transaction error"
            )

            raise

    # ============================================================
    # Internal Helpers
    # ============================================================

    def _get_session(
        self,
        session_id,
        user_id,
        include_deleted=False
    ):

        query = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )

        if not include_deleted:

            query = query.filter(
                ChatSession.is_deleted == False
            )

        session = self._execute_db(
            query.first
        )

        if session is None:

            raise SessionNotFoundError(
                "Session not found."
            )

        return session

    def _get_analysis(
        self,
        analysis_id
    ):

        query = (
            self.db.query(Analysis)
            .filter(
                Analysis.id == analysis_id
            )
        )

        analysis = self._execute_db(
            query.first
        )

        if analysis is None:

            raise AnalysisNotFoundError(
                "Analysis not found."
            )

        return analysis

    def _refresh(
        self,
        model
    ):

        return self._refresh_model(
            model
        )

    # ============================================================
    # Session Repository
    # ============================================================

    def create_session(
        self,
        user_id,
        title="New Chat",
        ticker=None
    ):

        session = ChatSession(
            user_id=user_id,
            title=title,
            ticker=ticker
        )

        with self.transaction():

            self.db.add(session)

            self._flush()

        return self._refresh(session)

    def get_session(
        self,
        session_id,
        user_id
    ):

        return self._get_session(
            session_id,
            user_id
        )

    def session_exists(
        self,
        session_id,
        user_id
    ):

        query = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_deleted == False
            )
        )

        count = self._execute_db(
            query.count
        )

        return count > 0

    def session_belongs_to_user(
        self,
        session_id,
        user_id
    ):

        return self.session_exists(
            session_id,
            user_id
        )

    def get_user_sessions(
        self,
        user_id,
        page=1,
        page_size=20
    ):

        offset = (
            (page - 1) * page_size
        )

        query = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.user_id == user_id,
                ChatSession.is_deleted == False
            )
            .order_by(
                ChatSession.updated_at.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        return self._execute_db(
            query.all
        )

    def update_session(
        self,
        session_id,
        user_id,
        title=None,
        ticker=None
    ):

        session = self._get_session(
            session_id,
            user_id
        )

        if title is not None:
            session.title = title

        if ticker is not None:
            session.ticker = ticker

        with self.transaction():

            self._flush()

        return self._refresh(session)

    def soft_delete_session(
        self,
        session_id,
        user_id
    ):

        session = self._get_session(
            session_id,
            user_id
        )

        session.is_deleted = True

        with self.transaction():

            self._flush()

    def restore_session(
        self,
        session_id,
        user_id
    ):

        session = self._get_session(
            session_id,
            user_id,
            include_deleted=True
        )

        session.is_deleted = False

        with self.transaction():

            self._flush()

        return self._refresh(session)

    def hard_delete_session(
        self,
        session_id,
        user_id
    ):

        session = self._get_session(
            session_id,
            user_id,
            include_deleted=True
        )

        with self.transaction():

            self.db.delete(session)

    # ============================================================
    # Message Repository
    # ============================================================

    def save_message(
        self,
        session_id,
        user_id,
        role,
        content,
        metadata=None
    ):

        self._get_session(
            session_id,
            user_id
        )

        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )

        with self.transaction():

            self.db.add(message)

            self._flush()

        return self._refresh(message)

    def save_messages_bulk(
        self,
        session_id,
        user_id,
        messages
    ):

        self._get_session(
            session_id,
            user_id
        )

        objects = []

        for item in messages:

            objects.append(
                Message(
                    session_id=session_id,
                    role=item["role"],
                    content=item["content"],
                    metadata=item.get(
                        "metadata",
                        {}
                    )
                )
            )

        with self.transaction():

            self.db.add_all(objects)

            self._flush()

        return objects

    def get_chat_history(
        self,
        session_id,
        user_id
    ):

        self._get_session(
            session_id,
            user_id
        )

        query = (
            self.db.query(Message)
            .filter(
                Message.session_id == session_id
            )
            .order_by(
                Message.created_at.asc()
            )
        )

        return self._execute_db(
            query.all
        )

    def get_latest_message(
        self,
        session_id,
        user_id
    ):

        self._get_session(
            session_id,
            user_id
        )

        query = (
            self.db.query(Message)
            .filter(
                Message.session_id == session_id
            )
            .order_by(
                Message.created_at.desc()
            )
        )

        return self._execute_db(
            query.first
        )

    def message_count(
        self,
        session_id,
        user_id
    ):

        self._get_session(
            session_id,
            user_id
        )

        query = (
            self.db.query(Message)
            .filter(
                Message.session_id == session_id
            )
        )

        return self._execute_db(
            query.count
        )

    def delete_messages(
        self,
        session_id,
        user_id
    ):

        self._get_session(
            session_id,
            user_id,
            include_deleted=True
        )

        query = (
            self.db.query(Message)
            .filter(
                Message.session_id == session_id
            )
        )

        with self.transaction():

            self._execute_db(
                query.delete
            )

    def search_messages(
        self,
        session_id,
        user_id,
        keyword
    ):

        self._get_session(
            session_id,
            user_id
        )

        query = (
            self.db.query(Message)
            .filter(
                Message.session_id == session_id,
                Message.content.ilike(
                    f"%{keyword}%"
                )
            )
            .order_by(
                Message.created_at.asc()
            )
        )

        return self._execute_db(
            query.all
        )

    # ============================================================
    # Analysis Repository
    # ============================================================
    from fastapi.encoders import jsonable_encoder

    def save_analysis(
            self,
            session_id,
            user_id,
            analysis_data: dict
    ):
        # -------------------------------------------------
        # Ensure session exists and belongs to user
        # -------------------------------------------------

        self._get_session(
            session_id,
            user_id
        )

        # -------------------------------------------------
        # Required fields
        # -------------------------------------------------

        query = analysis_data.get("query")
        ticker = analysis_data.get("ticker")

        if not query:
            raise ValueError(
                "Analysis query is required."
            )

        if not ticker:
            raise ValueError(
                "Analysis ticker is required."
            )

        # -------------------------------------------------
        # Convert JSONB data to JSON-safe structures
        # -------------------------------------------------

        market_analysis = jsonable_encoder(
            analysis_data.get(
                "market_analysis",
                {}
            )
        )

        fundamentals_analysis = jsonable_encoder(
            analysis_data.get(
                "fundamentals_analysis",
                {}
            )
        )

        news_analysis = jsonable_encoder(
            analysis_data.get(
                "news_analysis",
                []
            )
        )

        strategy_analysis = jsonable_encoder(
            analysis_data.get(
                "strategy_analysis",
                {}
            )
        )

        # -------------------------------------------------
        # Create analysis record
        # -------------------------------------------------

        analysis = Analysis(
            session_id=session_id,

            query=query,

            ticker=ticker,

            company_name=analysis_data.get(
                "company_name"
            ),

            market_analysis=market_analysis,

            fundamentals_analysis=(
                fundamentals_analysis
            ),

            news_analysis=news_analysis,

            strategy_analysis=(
                strategy_analysis
            ),

            llm_report=analysis_data.get(
                "llm_report"
            )
        )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        with self.transaction():
            self.db.add(analysis)
            self._flush()

        return self._refresh(
            analysis
        )
    def get_analysis(
        self,
        analysis_id,
        user_id
    ):

        query = (
            self.db.query(Analysis)
            .join(ChatSession)
            .filter(
                Analysis.id == analysis_id,
                ChatSession.user_id == user_id
            )
        )

        analysis = self._execute_db(
            query.first
        )

        if analysis is None:

            raise AnalysisNotFoundError(
                "Analysis not found."
            )

        return analysis

    def get_latest_analysis(
        self,
        session_id,
        user_id
    ):

        self._get_session(
            session_id,
            user_id
        )

        query = (
            self.db.query(Analysis)
            .filter(
                Analysis.session_id == session_id
            )
            .order_by(
                Analysis.created_at.desc()
            )
        )

        return self._execute_db(
            query.first
        )

    def get_session_analyses(
        self,
        session_id,
        user_id
    ):

        self._get_session(
            session_id,
            user_id
        )

        query = (
            self.db.query(Analysis)
            .filter(
                Analysis.session_id == session_id
            )
            .order_by(
                Analysis.created_at.desc()
            )
        )

        return self._execute_db(
            query.all
        )

    def update_analysis(
        self,
        analysis_id,
        user_id,
        llm_report
    ):

        analysis = self.get_analysis(
            analysis_id,
            user_id
        )

        analysis.llm_report = llm_report

        with self.transaction():

            self._flush()

        return self._refresh(analysis)

    def delete_analysis(
        self,
        analysis_id,
        user_id
    ):

        analysis = self.get_analysis(
            analysis_id,
            user_id
        )

        with self.transaction():

            self.db.delete(analysis)

    # ============================================================
    # User Repository
    # ============================================================

    def create_user(
        self,
        username,
        email,
        password_hash
    ):

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_verified=False
        )

        with self.transaction():

            self.db.add(user)

            self._flush()

        return self._refresh(user)

    def get_user_by_id(
        self,
        user_id
    ):

        query = (
            self.db.query(User)
            .filter(
                User.id == user_id
            )
        )

        user = self._execute_db(
            query.first
        )

        if user is None:

            raise UserNotFoundError(
                "User not found."
            )

        return user

    def get_user_by_email(
        self,
        email
    ):

        query = (
            self.db.query(User)
            .filter(
                User.email == email
            )
        )

        return self._execute_db(
            query.first
        )

    def get_user_by_username(
        self,
        username
    ):

        query = (
            self.db.query(User)
            .filter(
                User.username == username
            )
        )

        return self._execute_db(
            query.first
        )

    def update_user(
        self,
        user_id,
        **kwargs
    ):

        user = self.get_user_by_id(
            user_id
        )

        allowed_fields = {
            "username",
            "email"
        }

        for key, value in kwargs.items():

            if key in allowed_fields:

                setattr(
                    user,
                    key,
                    value
                )

        with self.transaction():

            self._flush()

        return self._refresh(user)

    def update_password_hash(
            self,
            user_id,
            password_hash,
    ):
        user = self.get_user_by_id(
            user_id
        )

        user.password_hash = password_hash

        with self.transaction():
            self._flush()

        return self._refresh(
            user
        )


    def change_password(
        self,
        user_id,
        password_hash
    ):

        user = self.get_user_by_id(
            user_id
        )

        user.password_hash = password_hash

        with self.transaction():

            self._flush()

        return self._refresh(user)

    def create_password_reset_token(
            self,
            user_id,
            token_hash,
            expires_at,
    ):
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            attempts=0,
            used=False,
        )

        with self.transaction():
            self.db.add(reset_token)
            self._flush()

        return self._refresh(
            reset_token
        )

    def get_active_password_reset_token(
            self,
            user_id,
    ):
        query = (
            self.db.query(
                PasswordResetToken
            )
            .filter(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used == False,
            )
            .order_by(
                PasswordResetToken.created_at.desc()
            )
        )

        return self._execute_db(
            query.first
        )


    ## invalidate existing reset tokens

    def invalidate_password_reset_tokens(
            self,
            user_id,
    ):
        query = (
            self.db.query(
                PasswordResetToken
            )
            .filter(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used == False,
            )
        )

        records = self._execute_db(
            query.all
        )

        for record in records:
            record.used = True

        if records:
            with self.transaction():
                self._flush()

        return len(records)


    ## Increment failed attempts

    def increment_password_reset_attempts(
            self,
            token_id,
    ):
        reset_token = self._execute_db(
            lambda: (
                self.db.query(
                    PasswordResetToken
                )
                .filter(
                    PasswordResetToken.id == token_id
                )
                .first()
            )
        )

        if reset_token is None:
            raise ValueError(
                "Password reset token not found."
            )

        reset_token.attempts += 1

        with self.transaction():
            self._flush()

        return self._refresh(
            reset_token
        )


    ## Mark reset token as used.

    def mark_password_reset_token_used(
            self,
            token_id,
    ):
        reset_token = self._execute_db(
            lambda: (
                self.db.query(
                    PasswordResetToken
                )
                .filter(
                    PasswordResetToken.id == token_id
                )
                .first()
            )
        )

        if reset_token is None:
            raise ValueError(
                "Password reset token not found."
            )

        reset_token.used = True

        with self.transaction():
            self._flush()

        return self._refresh(
            reset_token
        )

    def mark_user_verified(self, user_id):
        user = self.get_user_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        user.is_verified = True

        with self.transaction():
            self._flush()

        return self._refresh(user)

    def create_email_verification(
            self,
            user_id,
            otp_hash,
            expires_at,
    ):
        verification = EmailVerification(
            user_id=user_id,
            otp_hash=otp_hash,
            expires_at=expires_at,
            attempts=0,
            used=False,
        )

        with self.transaction():
            self.db.add(verification)
            self._flush()

        return self._refresh(
            verification
        )


## This retrieves the current unused OTP record for a particular user.
    def get_active_email_verification(
            self,
            user_id,
    ):
        query = (
            self.db.query(
                EmailVerification
            )
 ## Find verification records belonging to this user that have not already been used
            .filter(
                EmailVerification.user_id == user_id,
                EmailVerification.used == False,
            )
##puts the newest OTP first.
            .order_by(
                EmailVerification.created_at.desc()
            )
        )
## returns the most recent active OTP.
        return self._execute_db(
            query.first
        )

##Once the OTP has been successfully verified, we must make sure the same OTP cannot be reused.

## This function retrieves the verification record and then saves them
    def mark_email_verification_used(
            self,
            verification_id,
    ):
        verification = (
            self._execute_db(
                lambda: (
                    self.db.query(
                        EmailVerification
                    )
                    .filter(
                        EmailVerification.id
                        == verification_id
                    )
                    .first()
                )
            )
        )

        if verification is None:
            raise ValueError(
                "Email verification record not found."
            )

        verification.used = True

        with self.transaction():
            self._flush()

        return self._refresh(
            verification
        )

## This tracks failed OTP attempts.
    def increment_email_verification_attempts(
            self,
            verification_id,
    ):
        verification = (
            self._execute_db(
                lambda: (
                    self.db.query(
                        EmailVerification
                    )
                    .filter(
                        EmailVerification.id
                        == verification_id
                    )
                    .first()
                )
            )
        )

        if verification is None:
            raise ValueError(
                "Email verification record not found."
            )

        verification.attempts += 1

        with self.transaction():
            self._flush()

        return self._refresh(
            verification
        )

## if the user resends an OTP, the previous OTP and the new OTP should not both be valid,therefore
## all unused verifications are made invalid and the new OTP is created
    def invalidate_email_verifications(
            self,
            user_id,
    ):
        query = (
            self.db.query(
                EmailVerification
            )
            .filter(
                EmailVerification.user_id == user_id,
                EmailVerification.used == False,
            )
        )

        records = self._execute_db(
            query.all
        )

        for record in records:
            record.used = True

        if records:
            with self.transaction():
                self._flush()

        return len(records)
    def delete_user(
        self,
        user_id
    ):

        user = self.get_user_by_id(
            user_id
        )

        with self.transaction():

            self.db.delete(user)

