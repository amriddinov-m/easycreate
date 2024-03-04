import json
from loguru import logger
from functools import wraps
from json import JSONDecodeError

from loader import redis


# TODO: I think we should migrate to pickle instead json module. Yeah, I known, pickle is not safe

"""
def aio_redis_cache(expire_time: int = 60 * 10):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.trace(f"{expire_time=}")
            # Serialize the arguments and function name as a key for Redis
            key = "{}-{}".format(func.__name__, ",".join(str(arg) for arg in args))
            logger.trace(f"REDIS key: {key}")
            result = await redis_storage.get(key)

            if result is not None:
                # If the result is found in Redis cache, deserialize and return it
                result_raw = pickle.loads(result)
                logger.trace("Result found in REDIS")
            else:
                logger.trace("Result not found in REDIS")
                # If the result is not found in Redis cache, call the original function
                result_raw = await func(*args, **kwargs)
                result = pickle.dumps(result_raw)
                # Store the result in Redis with an expiration time
                await redis_storage.setex(key, expire_time, result)

            return result_raw

        return wrapper

    return decorator
"""


def redis_cache(ex: int, key: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if _val := await redis.get(key):
                try:
                    _val = json.loads(_val)
                except JSONDecodeError as ex:
                    logger.exception(f"Error while parsing cache value: {_val}", exc_info=ex)
            else:
                _val = await func(*args, **kwargs)
                _val_to_cache = _val
                if isinstance(_val, dict):
                    _val_to_cache = json.dumps(_val)
                elif isinstance(_val, str):
                    try:
                        _val = json.loads(_val)
                    except JSONDecodeError:
                        logger.exception(f"Error while parsing cache value: {_val}", exc_info=ex)
                else:
                    _val = str(_val)
                    _val_to_cache = _val
                await redis.set(key, _val_to_cache, ex=ex)
            return _val

        return wrapper

    return decorator
