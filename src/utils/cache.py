import time
from typing import Any, Callable, TypeVar
from functools import wraps

T = TypeVar("T")

# Simple in-memory cache with TTL (Time To Live)
_cache_store = {}


def cache(ttl_seconds: int = 300):
    """
    Decorator to cache function results with TTL (Time To Live).

    Args:
        ttl_seconds: Cache duration in seconds (default: 300 = 5 minutes)

    Example:
        @cache(ttl_seconds=600)
        def get_categories():
            return expensive_operation()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache_key = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create a unique key including arguments (for simple cases)
            full_key = cache_key
            if args or kwargs:
                full_key = f"{cache_key}:{args}:{kwargs}"

            now = time.time()

            # Check if cached result is still valid
            if full_key in _cache_store:
                cached_value, timestamp = _cache_store[full_key]
                if now - timestamp < ttl_seconds:
                    return cached_value

            # Call the actual function and cache the result
            result = func(*args, **kwargs)
            _cache_store[full_key] = (result, now)

            return result

        return wrapper

    return decorator


def clear_cache(pattern: str | None = None):
    """
    Clear cache entries.

    Args:
        pattern: Optional pattern to match cache keys (partial match)
                If None, clears all cache
    """
    global _cache_store

    if pattern is None:
        _cache_store.clear()
    else:
        keys_to_delete = [k for k in _cache_store.keys() if pattern in k]
        for key in keys_to_delete:
            del _cache_store[key]
