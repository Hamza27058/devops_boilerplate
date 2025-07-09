import json
from datetime import date
from redis import Redis
import logging

logger = logging.getLogger(__name__)

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def cache_user_data(redis_client: Redis, key: str, cache_data: list, ttl: int = 3600):
    """
    Cache a list of user data under the specified key with a TTL.
    Uses a custom JSON serializer to handle date objects.
    """
    try:
        serialized_data = json.dumps(cache_data, default=json_serializer)
        redis_client.set(key, serialized_data, ex=ttl)
        logger.info(f"Successfully cached data for key: {key}")
    except TypeError as e:
        logger.error(f"Failed to serialize data for caching: {e}")
        raise

def get_cached_user_data(redis_client: Redis, key: str) -> list | None:
    """
    Retrieve cached data for the specified key.
    """
    try:
        cached_data = redis_client.get(key)
        if cached_data:
            logger.info(f"Cache hit for key: {key}")
            return json.loads(cached_data)
        logger.info(f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve or parse cached data for key {key}: {e}")
        return None

