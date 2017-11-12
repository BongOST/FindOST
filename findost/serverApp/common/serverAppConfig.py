# -*- coding:utf-8 -*-
__author__ = 'LexusLee'
"""
该模块用于保存系统的常量数据
"""

from foundation.enum import Enum
from foundation import const

REDIS_DATA_TTL = 3600  # redis中键值的生存时间

COOKIE_DATA_TTL = 1  # cookie中键值的生存时间

TOKEN_USER_ID = "USER_ID"  # token 对应的用户id,包括高级用户、普通用户、游客

TOKEN_CREATE_TIME = "CT"  # token 创建时间

TOKEN_DEADLINE_TIME = "DT"  # token 失效时间

TOKEN_ROLE = "ROLE"  # token的角色

TOKEN_COOKIE_EXPIRES_DAYS = 30  # 单位天，token的有效期，也是token在浏览器中的生存周期

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 30  # 秒

CANCEL_DELAY_TIME = 3600  # 单位s

PAGE_LENGTH = 2  # 页数大少

# 设备类型
class _Device(Enum):
    """
    模拟枚举设备类型
    """
    def __init__(self):
        self.MOBILE = 0
        self.PC = 1
DEVICE_TYPE = _Device()
