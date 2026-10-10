from pathlib import Path
import argparse
from sqlalchemy.orm import configure_mappers
import os
from Backend.database.connection import SessionLocal
from Backend.database.messages import Message


from Backend.database.user_table import User

from Backend.database.sessions_table import (
    Session as DBSession
)

from Backend.database.email_verification import (
    EmailVerification
)

from Backend.database.password_reset import (
    PasswordResetToken
)

from Backend.database.analysis import (
    Analysis
)

from Backend.database.Analysis_vector import (
    AnalysisVector
)




DEFAULT_OUTPUT = Path(
    "Backend/tests/performance/perf_sessions.txt"
)


def create_performance_sessions(
    email: str,
    count: int,
    ticker: str,
    output_file: Path,
):
    if count < 1:
        raise ValueError(
            "Session count must be at least 1."
        )

    db = SessionLocal()

    try:
        # =================================================
        # FIND EXISTING PERFORMANCE USER
        # =================================================

        user = (
            db.query(User)
            .filter(
                User.email == email
            )
            .first()
        )

        if user is None:
            raise RuntimeError(
                f"No user found with email: {email}"
            )

        print(
            f"Found user: {user.email}"
        )

        print(
            f"User ID: {user.id}"
        )

        # =================================================
        # CREATE UNIQUE SESSIONS
        # =================================================

        sessions = []

        for number in range(
            1,
            count + 1
        ):
            session = DBSession(
                user_id=user.id,
                title=(
                    f"Locust Performance "
                    f"Session {number}"
                ),
                ticker=ticker,
            )

            db.add(
                session
            )

            sessions.append(
                session
            )

        # Generates UUIDs before commit.
        db.flush()

        session_ids = [
            str(session.id)
            for session in sessions
        ]

        db.commit()

        # =================================================
        # WRITE SESSION IDs TO FILE
        # =================================================

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file.write_text(
            "\n".join(
                session_ids
            ),
            encoding="utf-8"
        )

        print()
        print(
            f"Created {len(session_ids)} "
            f"performance-test sessions."
        )

        print(
            f"Saved session IDs to:"
        )

        print(
            output_file.resolve()
        )

        print()

        for index, session_id in enumerate(
            session_ids,
            start=1
        ):
            print(
                f"{index:02d}: {session_id}"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Create persistent sessions "
            "for Locust performance testing."
        )
    )

    parser.add_argument(
        "--email",
        default=os.environ.get(
            "PERF_EMAIL"
        ),
        help=(
            "Existing performance-test "
            "user email."
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        default=30,
        help=(
            "Number of sessions to create. "
            "Default: 30."
        ),
    )

    parser.add_argument(
        "--ticker",
        default="TSLA",
        help=(
            "Ticker attached to the "
            "performance sessions."
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT
        ),
        help=(
            "File where session UUIDs "
            "will be stored."
        ),
    )

    args = parser.parse_args()

    if not args.email:
        raise RuntimeError(
            "No email supplied. Set PERF_EMAIL "
            "or use --email."
        )

    create_performance_sessions(
        email=args.email,
        count=args.count,
        ticker=args.ticker,
        output_file=Path(
            args.output
        ),
    )


if __name__ == "__main__":
    main()