import uuid

from sqlalchemy import (
    Column,
    Text,
    String,
    DateTime,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import (
    UUID,
    JSONB
)

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from Backend.database.connection import Base


class Analysis(Base):

    __tablename__ = "analyses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=False
    )

    ticker = Column(
        String,
        nullable=False
    )

    company_name = Column(
        String
    )

    query = Column(
        Text,
        nullable=False
    )

    market_analysis = Column(
        JSONB
    )

    fundamentals_analysis = Column(
        JSONB
    )

    news_analysis = Column(
        JSONB
    )

    strategy_analysis = Column(
        JSONB
    )

    llm_report = Column(
        Text
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    session = relationship(
        "Session",
        back_populates="analyses"
    )

    vectors = relationship(
        "AnalysisVector",
        back_populates="analysis",
        cascade="all, delete-orphan"
    )