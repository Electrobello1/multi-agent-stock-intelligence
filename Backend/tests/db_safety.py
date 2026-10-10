from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[2]


def supabase_project_ref(url):
    """Recognize both direct and pooler Supabase URLs."""

    if url.host and url.host.startswith("db."):
        return url.host.split(".")[1]

    username = url.username or ""

    if username.startswith("postgres."):
        return username.split(".", 1)[1]

    return None


def get_test_database_url():

    test_config = dotenv_values(
        ROOT / ".env.test"
    )

    production_config = dotenv_values(
        ROOT / ".env"
    )

    if test_config.get("CONFIRM_ISOLATED_TEST_DB") != "YES":
        raise RuntimeError(
            "Test database has not been explicitly confirmed."
        )

    test_url = test_config.get("TEST_DATABASE_URL")
    production_url = production_config.get("DATABASE_URL")

    if not test_url or not production_url:
        raise RuntimeError(
            "Both production and test database URLs must be configured."
        )

    test = make_url(test_url)
    production = make_url(production_url)

    # Reject the same database, even if credentials differ.
    if (
        test.host == production.host
        and test.database == production.database
    ):
        raise RuntimeError(
            "Test database must be separate from production."
        )

    # Also detect the same Supabase project when one URL
    # uses the direct connection and the other uses a pooler.
    test_ref = supabase_project_ref(test)
    production_ref = supabase_project_ref(production)

    if (
        test_ref
        and production_ref
        and test_ref == production_ref
    ):
        raise RuntimeError(
            "Test and production URLs point to the same Supabase project."
        )

    return test_url