import uuid

from sqlalchemy import (
    Column,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from Backend.database.connection import Base


class PasswordResetToken(Base):

    __tablename__ = "password_reset_tokens"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    otp_hash = Column(
        String,
        nullable=False
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False
    )
    attempts = Column(
        Integer,
        default=0
    )

    is_expired = Column(
        Boolean,
        default=False
    )

    used = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="password_reset_tokens"
    )


