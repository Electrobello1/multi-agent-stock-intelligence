from logging.config import fileConfig

from alembic import context

from Backend.database.connection import (
    Base,
    engine
)

# Import all models so SQLAlchemy registers them
# in Base.metadata before Alembic checks for changes.
from Backend.database.user_table import User
from Backend.database.sessions_table import Session
from Backend.database.analysis import Analysis
from Backend.database.Analysis_vector import AnalysisVector
from Backend.database.email_verification import EmailVerification
from Backend.database.password_reset import PasswordResetToken
from Backend.database.messages import Message
from Backend.database.Asset_table import Asset
config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    url = str(engine.url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations using the application's SQLAlchemy engine.
    """

    with engine.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()