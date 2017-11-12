#!/usr/bin/env python
# -*- encoding:utf-8 -*-
__author__ = 'LexusLee'
"""
该模块是日志模块，负责记录整个应用的日志信息，通过继承threading.Thread类实现异步写日志，外部对象只需将日志信息交给该模块，然后直接返回，
无需等待将日志信息写到文件中，而是由该模块负责将日志信息写到文件中去，从而提高了写日志的速度
"""

import logging.config
import os
import yaml


from foundation import const

BASE_DIR = os.path.dirname(__file__)
if const.env == "development":
    log_config_path = os.path.abspath(os.path.join(BASE_DIR, os.pardir, 'configureFiles/development/appLogConf.yaml'))
    logging.config.dictConfig(yaml.load(open(log_config_path, 'r')))  # 加载日志配置文件
elif const.env == "production":
    log_config_path = os.path.abspath(os.path.join(BASE_DIR, os.pardir, 'configureFiles/production/appLogConf.yaml'))
    logging.config.dictConfig(yaml.load(open(log_config_path, 'r')))  # 加载日志配置文件
elif const.env == "test":
    log_config_path = os.path.abspath(os.path.join(BASE_DIR, os.pardir, 'configureFiles/test/appLogConf.yaml'))
    logging.config.dictConfig(yaml.load(open(log_config_path, 'r')))  # 加载日志配置文件
else:
    print '环境错误，只能是development，production,test'
logger = logging.getLogger("intlongLogger")

