import hashlib
import hmac
import os
import secrets

from datetime import datetime, timedelta, timezone


OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


class OTPService:
    """
    Handles OTP generation, hashing, and verification.

    The plaintext OTP is never stored in the database.
    """

    def __init__(
        self,
        secret_key: str | None = None
    ):
        self.secret_key = (
            secret_key
            or os.getenv("OTP_SECRET_KEY")
        )

        if not self.secret_key:
            raise RuntimeError(
                "OTP_SECRET_KEY is not configured."
            )

    # ======================================
    # GENERATE OTP
    # ======================================

    def generate_otp(self) -> str:
        """
        Generate a cryptographically secure
        six-digit OTP.
        """

        return str(
            secrets.randbelow(
                10 ** OTP_LENGTH
            )
        ).zfill(
            OTP_LENGTH
        )

    # ======================================
    # HASH OTP
    # ======================================

    def hash_otp(
        self,
        otp: str
    ) -> str:
        """
        Hash the OTP using a server-side secret.

        The plaintext OTP is never stored.
        """

        message = otp.encode(
            "utf-8"
        )

        key = self.secret_key.encode(
            "utf-8"
        )

        return hmac.new(
            key,
            message,
            hashlib.sha256
        ).hexdigest()

    # ======================================
    # VERIFY OTP
    # ======================================

    def verify_otp(
        self,
        otp: str,
        stored_hash: str
    ) -> bool:
        """
        Verify a supplied OTP against
        the stored hash.
        """

        if not otp:
            return False

        if not otp.isdigit():
            return False

        if len(otp) != OTP_LENGTH:
            return False

        calculated_hash = self.hash_otp(
            otp
        )

        return hmac.compare_digest(
            calculated_hash,
            stored_hash
        )

    # ======================================
    # EXPIRATION
    # ======================================

    def get_expiry_time(self) -> datetime:
        """
        Return the expiration time for
        a newly generated OTP.
        """

        return (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                minutes=OTP_EXPIRY_MINUTES
            )
        )

    def is_expired(
        self,
        expires_at: datetime
    ) -> bool:
        """
        Determine whether an OTP has expired.
        """

        now = datetime.now(
            timezone.utc
        )

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        return now >= expires_at

    # ======================================
    # ATTEMPT LIMIT
    # ======================================

    def attempts_exceeded(
        self,
        attempts: int
    ) -> bool:
        """
        Determine whether the maximum number
        of verification attempts has been reached.
        """

        return attempts >= MAX_OTP_ATTEMPTS