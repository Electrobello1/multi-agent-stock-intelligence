import os

from collections import deque
from pathlib import Path
from threading import Lock

import requests

from locust import (
    HttpUser,
    task,
    between,
    events,
)


# =========================================================
# CONFIGURATION
# =========================================================

PERF_EMAIL = os.environ.get(
    "PERF_EMAIL"
)

PERF_PASSWORD = os.environ.get(
    "PERF_PASSWORD"
)


SESSION_FILE = Path(
    os.environ.get(
        "PERF_SESSION_FILE",
        "Backend/tests/performance/perf_sessions.txt"
    )
)


# =========================================================
# LOAD SESSION IDs
# =========================================================

def load_session_ids():

    if not SESSION_FILE.exists():
        raise RuntimeError(
            f"Session file not found: {SESSION_FILE}"
        )

    session_ids = [
        line.strip()
        for line in SESSION_FILE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if not session_ids:
        raise RuntimeError(
            f"No session IDs found in {SESSION_FILE}"
        )

    return session_ids


SESSION_POOL = deque(
    load_session_ids()
)

SESSION_LOCK = Lock()


# =========================================================
# SHARED JWT
# =========================================================

ACCESS_TOKEN = None


# =========================================================
# LOGIN ONCE BEFORE LOAD TEST STARTS
# =========================================================

@events.test_start.add_listener
def login_once(
    environment,
    **kwargs
):

    global ACCESS_TOKEN

    if not PERF_EMAIL:
        raise RuntimeError(
            "PERF_EMAIL is not set."
        )

    if not PERF_PASSWORD:
        raise RuntimeError(
            "PERF_PASSWORD is not set."
        )

    host = environment.host

    if not host:
        raise RuntimeError(
            "Locust host is not configured."
        )

    response = requests.post(
        f"{host}/auth/login",
        json={
            "email": PERF_EMAIL,
            "password": PERF_PASSWORD,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Performance-test login failed. "
            f"Status={response.status_code}, "
            f"Body={response.text}"
        )

    ACCESS_TOKEN = response.json().get(
        "access_token"
    )

    if not ACCESS_TOKEN:
        raise RuntimeError(
            "Login response did not contain access_token."
        )

    print(
        "Performance test authenticated successfully."
    )

    print(
        f"Loaded {len(SESSION_POOL)} "
        f"performance sessions."
    )


# =========================================================
# VIRTUAL USER
# =========================================================

class StockAppUser(HttpUser):

    wait_time = between(
        2,
        5
    )

    def on_start(self):

        # -------------------------------------------------
        # JWT was obtained ONCE at test startup.
        # -------------------------------------------------

        if not ACCESS_TOKEN:
            raise RuntimeError(
                "Performance JWT is not available."
            )

        self.headers = {
            "Authorization": (
                f"Bearer {ACCESS_TOKEN}"
            )
        }

        # -------------------------------------------------
        # Assign unique session
        # -------------------------------------------------

        with SESSION_LOCK:

            if not SESSION_POOL:
                raise RuntimeError(
                    "No unused performance sessions remain."
                )

            self.session_id = (
                SESSION_POOL.popleft()
            )

            remaining = len(
                SESSION_POOL
            )

        print(
            f"Assigned session: "
            f"{self.session_id} | "
            f"Remaining: {remaining}"
        )

    # =====================================================
    # CHAT LOAD
    # =====================================================

    @task(5)
    def chat_follow_up(self):

        with self.client.post(
            "/chat",
            json={
                "message": (
                    "Can you explain that further?"
                ),
                "session_id": self.session_id,
            },
            headers=self.headers,
            name="/chat [conversation]",
            catch_response=True,
        ) as response:

            if response.status_code == 429:

                response.failure(
                    "Rate limited: HTTP 429"
                )

                return

            if response.status_code != 200:

                response.failure(
                    f"HTTP "
                    f"{response.status_code}: "
                    f"{response.text}"
                )

                return

            try:
                body = response.json()

            except Exception:

                response.failure(
                    "Response was not valid JSON."
                )

                return

            if not body.get(
                "response"
            ):

                response.failure(
                    "Missing response field."
                )

                return

            response.success()

    # =====================================================
    # HEALTH CHECK
    # =====================================================

    @task(1)
    def health_check(self):

        with self.client.get(
            "/health",
            name="/health",
            catch_response=True,
        ) as response:

            if response.status_code != 200:

                response.failure(
                    f"Health endpoint returned "
                    f"{response.status_code}"
                )

                return

            response.success()