import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from Backend.database.connection import Base


class Session(Base):

    __tablename__ = "sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id"
        ),
        nullable=False
    )

    title = Column(
        String,
        nullable=False,
        default="New Chat"
    )

    ticker = Column(
        String,
        nullable=True
    )

    is_deleted = Column(
        Boolean,
        default=False
    )

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        back_populates="sessions"
    )

    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan"
    )



    analysis_vectors = relationship(
        "AnalysisVector",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    analyses=relationship(
        "Analysis",
        back_populates="session",
        cascade="all, delete-orphan"
    )