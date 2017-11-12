#!/usr/bin/python
# -*- coding:utf-8 -*-

__author__ = 'LexusLee'
"""
该模块模拟一个postgres连接池和一个thread线程池
"""

import datetime

import concurrent.futures
import momoko
import psycopg2.extras
from tornado import process
from tornado.ioloop import IOLoop

from foundation import const
from foundation.parseConfig import load_conf

load_conf('postgresql')

executor = concurrent.futures.ThreadPoolExecutor(max_workers=int(process.cpu_count()))  # 创建一个线程池

ioloop = IOLoop.instance()
# 创建数据库连接池
dbpool = momoko.Pool(
    dsn='dbname={dbname} user={user} password={pwd} host={host} port={port}'.format(
    dbname=const.postgresql.get("dbname"),
    user=const.postgresql.get("user"),
    pwd=const.postgresql.get("password"),
    host=const.postgresql.get("host"),
    port=const.postgresql.get("port")),
    cursor_factory=psycopg2.extras.RealDictCursor,
    size=int(const.postgresql.get("size")),
    max_size=int(const.postgresql.get("max_size")),
    raise_connect_errors=True if const.postgresql.get("raise_connect_errors") == 'True' else False,
    reconnect_interval=int(const.postgresql.get("reconnect_interval")),
    auto_shrink=True if const.postgresql.get("auto_shrink") == 'True' else False,
    shrink_period=datetime.timedelta(seconds=1),
    shrink_delay=datetime.timedelta(minutes=5),
    ioloop=ioloop
)

future = dbpool.connect()
ioloop.add_future(future, lambda f: ioloop.stop())
ioloop.start()
future.result()