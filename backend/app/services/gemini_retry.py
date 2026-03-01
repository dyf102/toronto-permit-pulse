"""
Retry utility for Gemini API calls with exponential backoff.
Handles 429 RESOURCE_EXHAUSTED errors by extracting the retry delay
from the error response and waiting accordingly.
"""
import re
import os
import time
import logging
from typing import Callable, TypeVar, Optional

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Default config
MAX_RETRIES = 5
BASE_DELAY = 2.0       # seconds
MAX_DELAY = 60.0        # cap at 60s
BACKOFF_FACTOR = 2.0


def _parse_retry_delay(error_message: str) -> Optional[float]:
    """
    Extract the retry delay from a Gemini 429 error.
    Looks for patterns like 'retryDelay': '1s' or 'Please retry in 15.01s'
    """
    # Pattern 1: retryDelay field
    match = re.search(r"retryDelay.*?(\d+\.?\d*)\s*s", error_message)
    if match:
        return float(match.group(1))

    # Pattern 2: "Please retry in Xs"
    match = re.search(r"retry in (\d+\.?\d*)\s*s", error_message, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return None


def retry_gemini_call(
    fn: Callable[[], T],
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
    max_delay: float = MAX_DELAY,
    on_retry: Optional[Callable[[int, float, str], None]] = None,
) -> T:
    """
    Execute a Gemini API call with automatic retry on 429 errors.
    In development mode, retries are disabled to fail fast.
    """
    if os.getenv("ENVIRONMENT") == "development":
        return fn()

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            error_msg = str(e)
            last_exception = e

            # Only retry on rate limit / resource exhausted errors
            is_rate_limit = any(
                indicator in error_msg
                for indicator in [
                    "429",
                    "RESOURCE_EXHAUSTED",
                    "rate limit",
                    "quota exceeded",
                    "Too Many Requests",
                ]
            )

            if not is_rate_limit or attempt >= max_retries:
                raise

            # Calculate delay: prefer server-suggested delay, else exponential backoff
            server_delay = _parse_retry_delay(error_msg)
            if server_delay is not None:
                delay = min(server_delay + 1.0, max_delay)  # add 1s safety margin
            else:
                delay = min(base_delay * (BACKOFF_FACTOR ** attempt), max_delay)

            reason = f"429 rate limit (attempt {attempt + 1}/{max_retries})"
            logger.warning(
                f"[retry] {reason} — waiting {delay:.1f}s before retry"
            )

            if on_retry:
                on_retry(attempt + 1, delay, reason)

            time.sleep(delay)

    # Should not reach here, but just in case
    raise last_exception  # type: ignore
