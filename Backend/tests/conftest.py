import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from Backend.tests.db_safety import (
    get_test_database_url
)
# -------------------------------------------------
# Register SQLAlchemy models
# -------------------------------------------------

from Backend.database.user_table import User
from Backend.database.sessions_table import Session as DBSession
from Backend.database.analysis import Analysis
from Backend.database.Analysis_vector import AnalysisVector
from Backend.database.email_verification import EmailVerification
from Backend.database.password_reset import PasswordResetToken
from Backend.database.messages import Message
from Backend.database.Asset_table import Asset
from sqlalchemy.orm import configure_mappers

@pytest.fixture(scope="session")
def test_engine():

    test_url = get_test_database_url()

    engine = create_engine(
        test_url,
        pool_pre_ping=True
    )

    # Check that Alembic migrations have been applied.
    with engine.connect() as connection:

        users_table = connection.execute(
            text("SELECT to_regclass('public.users')")
        ).scalar()

        if users_table is None:
            raise RuntimeError(
                "Test database schema is missing. "
                "Run the test Alembic migrations first."
            )

    yield engine

    engine.dispose()


@pytest.fixture
def test_db(test_engine):

    connection = test_engine.connect()

    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint"
    )

    try:
        yield session

    finally:

        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()




@pytest.fixture
def sample_state():
    """
    Reusable sample LangGraph state
    for unit and integration tests.
    """

    return {
        "query": "Analyse TSLA",

        "user_id": "test-user-id",

        "session_id": "test-session-id",

        "resolved_asset": {
            "ticker": "TSLA",
            "company_name": "Tesla, Inc."
        }
    }
@pytest.fixture(scope="session", autouse=True)
def validate_database_models():

    configure_mappers()
