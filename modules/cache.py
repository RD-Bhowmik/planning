"""
Simple in-memory cache to reduce database queries
"""
import time
from functools import wraps

# Cache storage: {key: {"data": value, "expires": timestamp}}
_cache = {}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = 30  # Cache for 30 seconds

def get_cached(key):
    """Get value from cache if not expired"""
    if key in _cache:
        entry = _cache[key]
        if time.time() < entry["expires"]:
            return entry["data"]
        else:
            # Expired, remove it
            del _cache[key]
    return None

def set_cache(key, value, ttl=CACHE_TTL):
    """Store value in cache with expiration"""
    _cache[key] = {
        "data": value,
        "expires": time.time() + ttl
    }

def invalidate_cache(key):
    """Remove a specific key from cache"""
    if key in _cache:
        del _cache[key]

def invalidate_user_cache(user_id):
    """Invalidate all cache entries for a specific user"""
    keys_to_delete = [k for k in _cache.keys() if str(user_id) in k]
    for key in keys_to_delete:
        del _cache[key]

def clear_cache():
    """Clear entire cache"""
    global _cache
    _cache = {}

def cached(ttl=CACHE_TTL):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = get_cached(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            set_cache(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

