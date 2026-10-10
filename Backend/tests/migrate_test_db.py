import os

from alembic import command
from alembic.config import Config

from Backend.tests.db_safety import (
    ROOT,
    get_test_database_url
)


def main():

    # Validate the test database before changing DATABASE_URL.
    test_url = get_test_database_url()

    # This change applies only to this Python process.
    os.environ["DATABASE_URL"] = test_url

    alembic_config = Config(
        str(ROOT / "alembic.ini")
    )

    command.upgrade(
        alembic_config,
        "head"
    )

    print("Test database migrations completed.")


if __name__ == "__main__":
    main()