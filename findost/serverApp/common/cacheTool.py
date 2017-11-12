# -*- coding:utf-8 -*-
__author__ = 'gui'
"""
这个模块主要负责缓存相关的处理，实现是对redis封装
"""

from tornado.gen import coroutine
import tornado.gen
import tornadoredis
from foundation import const

__redisHost = const.redis_app.get('host')
__redisPort = int(const.redis_app.get('port'))
__redisPassword = const.redis_app.get('password')


@coroutine
def set(redis, key, value, expire=None, pexpire=None, only_if_not_exists=False, only_if_exists=False):
    """

    :param key:
    :param value:
    :param expire:
    :param pexpire:
    :param only_if_not_exists:
    :param only_if_exists:
    :return:boolean
    """
    result = yield tornado.gen.Task(redis.set, key, value, expire=expire, pexpire=pexpire,
                               only_if_not_exists=only_if_not_exists, only_if_exists=only_if_exists)
    raise tornado.gen.Return(result)


@coroutine
def get(redis, key):
    """

    :param key:
    :return:key对应的值或None
    """
    result = yield tornado.gen.Task(redis.get, key)
    raise tornado.gen.Return(result)


@coroutine
def expire(redis, key, ttl):
    """

    :param key:
    :param ttl:
    :return:boolean
    """
    result = yield tornado.gen.Task(redis.expire, key, ttl)
    raise tornado.gen.Return(result)

@coroutine
def exists(redis, key):
    result = yield tornado.gen.Task(redis.exists, key)
    raise tornado.gen.Return(result)

@coroutine
def delete(redis, *keys, **kwargs):
    """
    :param keys:
    :param kwargs:
    :return:boolean
    """
    result = yield tornado.gen.Task(redis.delete, *keys, **kwargs)
    raise tornado.gen.Return(result)

@coroutine
def rpush(redis, key, *values, **kwargs):
    result = yield tornado.gen.Task(redis.rpush, key, *values, **kwargs)
    # result = yield redis.call("RPUSH", key, *values)
    raise tornado.gen.Return(result)

@coroutine
def lpop(redis, key):
    result = yield tornado.gen.Task(redis.lpop, key)
    raise tornado.gen.Return(result)

@coroutine
def llen(redis, key):
    result = yield tornado.gen.Task(redis.llen, key)
    raise tornado.gen.Return(result)

@coroutine
def lrange(redis, key, start, end):
    result  = yield tornado.gen.Task(redis.lrange, key, start, end)
    # result = yield redis.call("LRANGE", key, start, end)
    raise tornado.gen.Return(result)

@coroutine
def lindex(redis, key, index):
    result = yield tornado.gen.Task(redis.lindex, key, index)
    raise tornado.gen.Return(result)

@coroutine
def hset(redis, key, field, value):
    yield tornado.gen.Task(redis.hset, key, field, value)

@coroutine
def hget(redis, key, field):
    result = yield tornado.gen.Task(redis.hget, key, field)
    raise tornado.gen.Return(result)

@coroutine
def hmset(redis, key, mapping):
    yield tornado.gen.Task(redis.hmset, key, mapping)

@coroutine
def hmget(redis, key, *fields):
    result = yield tornado.gen.Task(redis.hmget, key, fields )
    raise tornado.gen.Return(result)

@coroutine
def hgetall(redis, key):
    result = yield tornado.gen.Task(redis.hgetall, key)
    # result = yield redis.call("HGETALL", key)
    raise tornado.gen.Return(result)

@coroutine
def sadd(redis, key, *members):
    result = yield tornado.gen.Task(redis.sadd( key, *members))
    raise tornado.gen.Return(result)

@coroutine
def srem(redis, key, *members):
    result = yield tornado.gen.Task(redis.srem,  key, *members)
    raise tornado.gen.Return(result)

@coroutine
def smembers(redis, key):
    result = yield tornado.gen.Task(redis.smembers, key)
    raise tornado.gen.Return(result)

def _get_redis_connection():
    redis_client = tornadoredis.Client(host=__redisHost, port=__redisPort, password=__redisPassword)
    redis_client.connect()
    return redis_client




