import logging
import time
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

def retry_with_backoff(max_attempts=3, initial_wait=1, max_wait=60):
    """
    Decorator for retrying functions with exponential backoff.
    Use this for R2/S3 operations specifically.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    wait_time = min(initial_wait * (2 ** (attempt - 1)), max_wait)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}). Retrying in {wait_time}s... Error: {e}")
                    time.sleep(wait_time)
        return wrapper
    return decorator

# Pipeline stage retry decorator - used across all worker modules
pipeline_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True
)