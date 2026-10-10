
import os
import time
import random

import requests
from dotenv import load_dotenv
from threading import BoundedSemaphore

from Backend.Resilience.breakers import (
    llm_breaker
)


load_dotenv()


# =========================================================
# LLM CONCURRENCY CONFIGURATION
# =========================================================

LLM_MAX_CONCURRENCY = int(
    os.getenv(
        "LLM_MAX_CONCURRENCY",
        "3"
    )
)

LLM_MAX_RETRIES = int(
    os.getenv(
        "LLM_MAX_RETRIES",
        "2"
    )
)

LLM_QUEUE_TIMEOUT = int(
    os.getenv(
        "LLM_QUEUE_TIMEOUT",
        "60"
    )
)


# =========================================================
# LLM CONCURRENCY GUARD
# =========================================================

LLM_SEMAPHORE = BoundedSemaphore(
    LLM_MAX_CONCURRENCY
)


# =========================================================
# OLLAMA CONFIGURATION
# =========================================================

OLLAMA_API_KEY = os.getenv(
    "OLLAMA_API_KEY"
)

OLLAMA_URL = (
    "https://ollama.com/api/generate"
)

OLLAMA_MODEL = (
    "gemma4:31b-cloud"
)


# =========================================================
# LLM GENERATION
# =========================================================

def generate_llm_response(
    system_prompt: str,
    user_prompt: str
):
    """
    Generate an LLM response through Ollama Cloud.

    The public interface matches LLMAgent:

        generate_llm_response(
            system_prompt=...,
            user_prompt=...
        )

    Production protections:

    - BoundedSemaphore limits concurrent Ollama calls.
    - Queue timeout prevents requests waiting forever.
    - Circuit breaker protects the external provider.
    - Transient 429 responses are retried with
      exponential backoff and jitter.
    """

    if not OLLAMA_API_KEY:
        raise RuntimeError(
            "OLLAMA_API_KEY is not configured."
        )

    payload = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False
    }

    headers = {
        "Authorization": (
            f"Bearer {OLLAMA_API_KEY}"
        ),
        "Content-Type": "application/json"
    }

    # -----------------------------------------------------
    # WAIT FOR AN AVAILABLE LLM CONCURRENCY SLOT
    # -----------------------------------------------------

    acquired = LLM_SEMAPHORE.acquire(
        timeout=LLM_QUEUE_TIMEOUT
    )

    if not acquired:
        raise RuntimeError(
            "LLM request queue is full. "
            "No Ollama concurrency slot became "
            "available before the queue timeout."
        )

    try:

        # -------------------------------------------------
        # OLLAMA REQUEST WITH RETRY
        # -------------------------------------------------

        for attempt in range(
            LLM_MAX_RETRIES + 1
        ):

            try:

                response = llm_breaker.call(
                    requests.post,
                    OLLAMA_URL,
                    json=payload,
                    headers=headers,
                    timeout=200
                )

                # -----------------------------------------
                # PROVIDER RATE LIMIT
                # -----------------------------------------

                if response.status_code == 429:

                    if attempt >= LLM_MAX_RETRIES:
                        response.raise_for_status()

                    retry_after = (
                        response.headers.get(
                            "Retry-After"
                        )
                    )

                    if (
                        retry_after
                        and retry_after.isdigit()
                    ):
                        delay = float(
                            retry_after
                        )

                    else:
                        delay = (
                            (2 ** attempt)
                            + random.uniform(
                                0.1,
                                0.5
                            )
                        )

                    time.sleep(
                        delay
                    )

                    continue

                # -----------------------------------------
                # OTHER HTTP ERRORS
                # -----------------------------------------

                response.raise_for_status()

                # -----------------------------------------
                # PARSE RESPONSE
                # -----------------------------------------

                data = response.json()

                generated_text = data.get(
                    "response"
                )

                if not generated_text:
                    raise RuntimeError(
                        "Ollama returned an empty response."
                    )

                return generated_text

            except requests.RequestException as e:

                # Retry transient network failures
                if attempt < LLM_MAX_RETRIES:

                    delay = (
                        (2 ** attempt)
                        + random.uniform(
                            0.1,
                            0.5
                        )
                    )

                    time.sleep(
                        delay
                    )

                    continue

                raise RuntimeError(
                    f"Ollama request failed: {e}"
                ) from e

            except (
                KeyError,
                TypeError,
                ValueError
            ) as e:

                raise RuntimeError(
                    f"Invalid Ollama response: {e}"
                ) from e

        raise RuntimeError(
            "Ollama request failed after "
            "all retry attempts."
        )

    finally:

        # -------------------------------------------------
        # ALWAYS RETURN THE SEMAPHORE SLOT
        # -------------------------------------------------

        LLM_SEMAPHORE.release()
