import os

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from Backend.services.email_validator import (
    EmailValidator,
)
import hashlib
import secrets
from Backend.services.otp_service import (
    OTPService,
)

from Backend.services.email_services import (
    EmailService,
)

from Backend.memory.postgres_memory import (
    PostgresMemory,
)


# ======================================
# CONFIGURATION
# ======================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

JWT_REFRESH_SECRET_KEY = os.getenv(
    "JWT_REFRESH_SECRET_KEY"
)

JWT_ALGORITHM= "HS256"

PASSWORD_RESET_EXPIRE_MINUTES = 15
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7


EMAIL_VERIFICATION_ENABLED = False


if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not configured."
    )


if not JWT_REFRESH_SECRET_KEY:
    raise RuntimeError(
        "JWT_REFRESH_SECRET_KEY is not configured."
    )


# ======================================
# PASSWORD HASHING
# ======================================

password_hasher = PasswordHasher()


class AuthService:

    def __init__(
        self,
        postgres_memory: PostgresMemory,
    ):
        self.postgres_memory = (
            postgres_memory
        )

        self.email_validator = (
            EmailValidator()
        )

        self.otp_service = OTPService()

        self.email_service = (
            EmailService()
            if EMAIL_VERIFICATION_ENABLED
            else None
        )

    # ==================================
    # PASSWORD
    # ==================================

    def hash_password(
        self,
        password: str,
    ) -> str:
        """
        Hash a password using Argon2id.
        """

        return password_hasher.hash(
            password
        )

    def verify_password(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        """
        Verify a password against an
        Argon2id hash.
        """

        try:
            return password_hasher.verify(
                password_hash,
                password,
            )

        except (
            VerifyMismatchError,
            VerificationError,
            InvalidHashError,
        ):
            return False

    def password_needs_rehash(
        self,
        password_hash: str,
    ) -> bool:
        """
        Check whether the stored Argon2id hash
        should be replaced using the current
        Argon2id parameters.
        """

        return password_hasher.check_needs_rehash(
            password_hash
        )

    def get_current_user(
            self,
            token: str
    ):
        payload = self.decode_access_token(token)

        user_id = payload["user_id"]

        user = self.postgres_memory.get_user_by_id(
            user_id
        )

        if user is None:
            raise ValueError(
                "User not found."
            )

        return user

    # ==================================
    # REGISTRATION
    # ==================================

    def register(
        self,
        username: str,
        email: str,
        password: str,
    ):

        email = email.strip().lower()

        # -------------------------------
        # Validate email
        # -------------------------------

        if not self.email_validator.validate(
            email
        ):
            raise ValueError(
                "Please provide a valid email address."
            )

        # -------------------------------
        # Check existing email
        # -------------------------------

        existing_user = (
            self.postgres_memory.get_user_by_email(
                email
            )
        )

        if existing_user is not None:
            raise ValueError(
                "Email is already registered."
            )

        # -------------------------------
        # Check existing username
        # -------------------------------

        existing_username = (
            self.postgres_memory.get_user_by_username(
                username
            )
        )

        if existing_username is not None:
            raise ValueError(
                "Username is already taken."
            )

        # -------------------------------
        # Hash password
        # -------------------------------

        password_hash = self.hash_password(
            password
        )

        # -------------------------------
        # Create user
        # -------------------------------

        user = (
            self.postgres_memory.create_user(
                username=username,
                email=email,
                password_hash=password_hash,
            )
        )

        # -------------------------------
        # Development mode
        # -------------------------------

        if not EMAIL_VERIFICATION_ENABLED:

            self.postgres_memory.mark_user_verified(
                user.id
            )

            return user

        # -------------------------------
        # Production verification
        # -------------------------------

        self._send_verification_otp(
            user
        )

        return user

    # ==================================
    # SEND VERIFICATION OTP
    # ==================================

    def _send_verification_otp(
        self,
        user,
    ):

        if self.email_service is None:
            raise RuntimeError(
                "Email verification is enabled "
                "but EmailService is unavailable."
            )

        # Invalidate previous OTPs
        self.postgres_memory.invalidate_email_verifications(
            user.id
        )

        # Generate OTP
        otp = self.otp_service.generate_otp()

        # Hash OTP
        otp_hash = self.otp_service.hash_otp(
            otp
        )

        # Expiration
        expires_at = (
            self.otp_service.get_expiry_time()
        )

        # Store verification record
        self.postgres_memory.create_email_verification(
            user_id=user.id,
            otp_hash=otp_hash,
            expires_at=expires_at,
        )

        # Send OTP
        self.email_service.send_verification_otp(
            to_email=user.email,
            otp=otp,
        )

    # ==================================
    # VERIFY EMAIL
    # ==================================

    def verify_email(
        self,
        email: str,
        otp: str,
    ):

        email = email.strip().lower()

        user = (
            self.postgres_memory.get_user_by_email(
                email
            )
        )

        if user is None:
            raise ValueError(
                "Invalid verification request."
            )

        if user.is_verified:
            return user

        verification = (
            self.postgres_memory
            .get_active_email_verification(
                user.id
            )
        )

        if verification is None:
            raise ValueError(
                "Verification code is invalid or expired."
            )

        if self.otp_service.attempts_exceeded(
            verification.attempts
        ):
            raise ValueError(
                "Maximum verification attempts exceeded."
            )

        if self.otp_service.is_expired(
            verification.expires_at
        ):
            raise ValueError(
                "Verification code has expired."
            )

        valid = self.otp_service.verify_otp(
            otp=otp,
            stored_hash=verification.otp_hash,
        )

        if not valid:

            self.postgres_memory.increment_email_verification_attempts(
                verification.id
            )

            raise ValueError(
                "Invalid verification code."
            )

        # Mark OTP as used
        self.postgres_memory.mark_email_verification_used(
            verification.id
        )

        # Mark user as verified
        user = self.postgres_memory.verify_email(
            user.id
        )

        return user

    # ==================================
    # RESEND OTP
    # ==================================

    def resend_verification_otp(
        self,
        email: str,
    ):

        if not EMAIL_VERIFICATION_ENABLED:
            raise ValueError(
                "Email verification is disabled."
            )

        email = email.strip().lower()

        user = (
            self.postgres_memory.get_user_by_email(
                email
            )
        )

        if user is None:
            raise ValueError(
                "Unable to process verification request."
            )

        if user.is_verified:
            raise ValueError(
                "Email is already verified."
            )

        self._send_verification_otp(
            user
        )

        return True

    # ==================================
    # LOGIN
    # ==================================

    def login(
        self,
        email: str,
        password: str,
    ):

        email = email.strip().lower()

        user = (
            self.postgres_memory.get_user_by_email(
                email
            )
        )

        if user is None:
            raise ValueError(
                "Invalid email or password."
            )

        password_valid = (
            self.verify_password(
                password,
                user.password_hash,
            )
        )

        if not password_valid:
            raise ValueError(
                "Invalid email or password."
            )

        if not user.is_verified:
            raise ValueError(
                "Please verify your email before logging in."
            )

        # ---------------------------------
        # Upgrade old Argon2id hash
        # ---------------------------------

        if self.password_needs_rehash(
            user.password_hash
        ):

            new_password_hash = (
                self.hash_password(
                    password
                )
            )

            self.postgres_memory.update_password_hash(
                user.id,
                new_password_hash,
            )

        # ---------------------------------
        # Create tokens
        # ---------------------------------

        access_token = (
            self.create_access_token(
                user.id
            )
        )

        refresh_token = (
            self.create_refresh_token(
                user.id
            )
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ==================================
    # ACCESS TOKEN
    # ==================================

    def create_access_token(
        self,
        user_id,
    ) -> str:

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            now
            + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )

        payload = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "type": "access",
            "iat": now,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )

    # ==================================
    # REFRESH TOKEN
    # ==================================

    def create_refresh_token(
        self,
        user_id,
    ) -> str:

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            now
            + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
        )

        payload = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            JWT_REFRESH_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )

    # ==================================
    # VERIFY ACCESS TOKEN
    # ==================================

    def decode_access_token(
        self,
        token: str,
    ):

        try:

            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[
                    JWT_ALGORITHM
                ],
            )

        except JWTError as e:

            raise ValueError(
                "Invalid or expired access token."
            ) from e

        if payload.get("type") != "access":
            raise ValueError(
                "Invalid token type."
            )

        user_id = payload.get(
            "user_id"
        )

        if not user_id:
            raise ValueError(
                "Invalid access token."
            )

        return payload

    # ==================================
    # VERIFY REFRESH TOKEN
    # ==================================

    def decode_refresh_token(
        self,
        token: str,
    ):

        try:

            payload = jwt.decode(
                token,
                JWT_REFRESH_SECRET_KEY,
                algorithms=[
                    JWT_ALGORITHM
                ],
            )

        except JWTError as e:

            raise ValueError(
                "Invalid or expired refresh token."
            ) from e

        if payload.get("type") != "refresh":
            raise ValueError(
                "Invalid token type."
            )

        user_id = payload.get(
            "user_id"
        )

        if not user_id:
            raise ValueError(
                "Invalid refresh token."
            )

        return payload

    # ==================================
    # REFRESH ACCESS TOKEN
    # ==================================

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> str:

        payload = (
            self.decode_refresh_token(
                refresh_token
            )
        )

        return self.create_access_token(
            payload["user_id"]
        )

    def generate_password_reset_token(
            self,
    ) -> str:
        """
        Generate a cryptographically random
        password-reset token.
        """

        return secrets.token_urlsafe(
            32
        )

    def hash_password_reset_token(
            self,
            token: str,
    ) -> str:
        """
        Hash the reset token before storing it.
        """

        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    def forgot_password(
            self,
            email: str,
    ):
        """
        Start the password-reset process.

        For security, this method returns the same
        external result whether or not the account exists.
        """

        email = email.strip().lower()

        user = (
            self.postgres_memory.get_user_by_email(
                email
            )
        )

        if user is None:
            return True

        if self.email_service is None:
            raise RuntimeError(
                "Password reset email service is not configured."
            )

        self.postgres_memory.invalidate_password_reset_tokens(
            user.id
        )

        token = (
            self.generate_password_reset_token()
        )

        token_hash = (
            self.hash_password_reset_token(
                token
            )
        )

        expires_at = (
                datetime.now(timezone.utc)
                + timedelta(
            minutes=PASSWORD_RESET_EXPIRE_MINUTES
        )
        )

        self.postgres_memory.create_password_reset_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.email_service.send_password_reset_email(
            to_email=user.email,
            token=token,
        )

        return True

    def change_password(
            self,
            user_id,
            current_password: str,
            new_password: str
    ):
        user = self.postgres_memory.get_user_by_id(
            user_id
        )

        if user is None:
            raise ValueError(
                "User not found."
            )

        current_password_valid = (
            self.verify_password(
                current_password,
                user.password_hash
            )
        )

        if not current_password_valid:
            raise ValueError(
                "Current password is incorrect."
            )

        new_password_hash = self.hash_password(
            new_password
        )

        self.postgres_memory.update_password_hash(
            user.id,
            new_password_hash
        )

        return True

    def reset_password(
            self,
            email: str,
            token: str,
            new_password: str,
    ):
        """
        Verify the password-reset token and replace
        the user's password.
        """

        email = email.strip().lower()

        user = (
            self.postgres_memory.get_user_by_email(
                email
            )
        )

        if user is None:
            raise ValueError(
                "Invalid password reset request."
            )

        reset_token = (
            self.postgres_memory
            .get_active_password_reset_token(
                user.id
            )
        )

        if reset_token is None:
            raise ValueError(
                "Invalid or expired reset token."
            )

        if reset_token.attempts >= 5:
            raise ValueError(
                "Maximum reset attempts exceeded."
            )

        expires_at = reset_token.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if datetime.now(timezone.utc) >= expires_at:
            raise ValueError(
                "Reset token has expired."
            )

        calculated_hash = (
            self.hash_password_reset_token(
                token
            )
        )

        if not secrets.compare_digest(
                calculated_hash,
                reset_token.token_hash,
        ):
            self.postgres_memory.increment_password_reset_attempts(
                reset_token.id
            )

            raise ValueError(
                "Invalid reset token."
            )

        new_password_hash = (
            self.hash_password(
                new_password
            )
        )

        self.postgres_memory.update_password_hash(
            user.id,
            new_password_hash,
        )

        self.postgres_memory.mark_password_reset_token_used(
            reset_token.id
        )

        return True


