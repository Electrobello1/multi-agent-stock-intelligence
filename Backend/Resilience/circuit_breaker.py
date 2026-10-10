import threading
import time
from enum import Enum
from functools import wraps


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a circuit is open and calls are blocked."""
    pass


class CircuitBreaker:
    """
    Thread-safe synchronous circuit breaker.

    CLOSED:
        Calls are allowed.

    OPEN:
        Calls are blocked until recovery_timeout expires.

    HALF_OPEN:
        Exactly one probe call is allowed. Successful probe closes
        the circuit; failed probe opens it again.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions=(Exception,),
    ):
        if failure_threshold <= 0:
            raise ValueError(
                "failure_threshold must be greater than zero."
            )

        if recovery_timeout <= 0:
            raise ValueError(
                "recovery_timeout must be greater than zero."
            )

        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None
        self._half_open_probe_in_progress = False

        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and self._opened_at is not None
                and (
                    time.monotonic() - self._opened_at
                    >= self.recovery_timeout
                )
            ):
                self._state = CircuitState.HALF_OPEN

            return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failure_count

    def _before_call(self) -> None:
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return

            if self._state == CircuitState.OPEN:
                if (
                    self._opened_at is not None
                    and (
                        time.monotonic() - self._opened_at
                        >= self.recovery_timeout
                    )
                ):
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is OPEN."
                    )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_probe_in_progress:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is HALF_OPEN "
                        "and a recovery probe is already running."
                    )

                self._half_open_probe_in_progress = True

    def _on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._opened_at = None
            self._state = CircuitState.CLOSED
            self._half_open_probe_in_progress = False

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._half_open_probe_in_progress = False

            if (
                self._failure_count
                >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()

    def call(
        self,
        function,
        *args,
        **kwargs,
    ):
        self._before_call()

        try:
            result = function(
                *args,
                **kwargs,
            )

        except self.expected_exceptions:
            self._on_failure()
            raise

        else:
            self._on_success()
            return result