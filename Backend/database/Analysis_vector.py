import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Text,
    Index
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from Backend.database.connection import Base


class AnalysisVector(Base):

    __tablename__ = "analysis_vectors"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "analyses.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "sessions.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    embedded_text = Column(
        Text,
        nullable=False
    )

    embedding = Column(
        Vector(384),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    analysis = relationship(
        "Analysis",
        back_populates="vectors"
    )

    user = relationship(
        "User",
        back_populates="analysis_vectors"
    )
    session = relationship(
        "Session",
        back_populates="analysis_vectors"
    )

    __table_args__ = (
        Index(
            "idx_vector_user",
            "user_id"
        ),
        Index(
            "idx_vector_session",
            "session_id"
        ),
        Index(
            "idx_vector_analysis",
            "analysis_id"
        ),
    )