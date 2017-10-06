#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'LexusLee'

"""
FindOST Backend main server
"""
import os
import sys

BASE_DIR = os.path.dirname(__file__)
top_files_path = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
sys.path.append(top_files_path)

# 解析命令行参数
from tornado.options import define, options, parse_command_line
from foundation import const

define("env", default="development", help="run on the given ip address", type=str)
define("port", default=8000, help="run on the given port", type=int)
parse_command_line()
const.env = options.env

# 加载系统配置文件
import foundation.parseConfig as parseConfig
parseConfig.load_config()

# 初始化设置
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

# 该部分引用python系统模块
import signal

# 该部分引用tornado模块
from tornado.ioloop import IOLoop
from tornado.web import url
from tornado.autoreload import add_reload_hook

# 该部分引用数据库连接
from serverApp.common.connectionPool import dbpool

# from tests.testhandler_for_authorityconf import TestHandler_for_authorityconf
# from tests.test_handler_for_authority import TestHandlerForAuthority

# 该部分引用测试部分test handler
if const.env == "development":
    test_handlers = [
        url(r"/v1/login", Login)
    ]
    logger.info("加载测试的handlers")
else:
    logger.info("忽略测试的handlers")
    test_handlers = []

# 该部分引用系统部分handler
handlers = [

]

settings = dict(
    cookie_secret=const.basic.get("cookie_secret", '56051215-9fb1-4ac8-800a-f52fa0308f58'),
    template_path=os.path.join(os.path.dirname(__file__), "template"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    debug=False if options.env == "production" else True,
)

handlers.extend(test_handlers)
app = tornado.web.Application(handlers, **settings)


def main():
    logger.info("服务器监听在" + const.basic.get("host", "") + ":" + str(options.port))
    logger.info("部署的环境是:" + options.env)
    logger.info("debug：" + str(settings["debug"]))
    add_reload_hook(do_before_autoreload)
    from tornado.httpserver import HTTPServer
    global server
    server = HTTPServer(app, xheaders=True)
    server.listen(port=options.port, address=const.basic.get("host", ""))
    IOLoop.current().start()

def do_before_autoreload():
    if not dbpool.closed:
        logger.info('autorealod:关闭postgresql连接池')
        dbpool.close()


def sig_handler(sig, frame):
    logger.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)


def shutdown():
    from serverApp.common.serverAppConfig import MAX_WAIT_SECONDS_BEFORE_SHUTDOWN
    logger.info('Stopping http server')
    server.stop()

    logger.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()

    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

    len_ioloop_timeouts = 1000 if settings['debug'] else 999

    def stop_loop():
        now = time.time()

        if now < deadline and \
                (len(io_loop._callbacks) > 0 or len(io_loop._timeouts) > len_ioloop_timeouts or len(io_loop._handlers) > 10):
            io_loop.add_timeout(now + 1, stop_loop)
            logger.info("Waiting for ioloop to be empty. has %d handlers left, has %d timeouts left, has %d callbacks left"
                    % (len(io_loop._handlers), len(io_loop._timeouts), len(io_loop._callbacks)))
        else:
            if not dbpool.closed:
                logger.info('关闭postgresql连接池,请等待3s')
                dbpool.close()
                io_loop.add_timeout(now + 3, stop_loop)
                return
            io_loop.stop()
            logger.info("Has %d handlers left, has %d timeouts left, has %d callbacks left"
                    % (len(io_loop._handlers), len(io_loop._timeouts), len(io_loop._callbacks)))
            logger.info('Shutdown')
    stop_loop()

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGQUIT, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    main()


