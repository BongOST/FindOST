# -*- coding:utf-8 -*-
__author__ = 'lee'
"""
数据库自定义异常
"""

class ExistError(Exception):
    def __init__(self, exist, message):
        self.exist = exist
        self.message = message

    def __str__(self):
        return repr(self.message)


class NotExistError(Exception):
    def __init__(self, notexist, message):
        self.notexist = notexist
        self.message = message

    def __str__(self):
        return repr(self.message)

class OutRangeError(Exception):
    def __init__(self, table, message):
        self.table = table
        self.message = message

    def __str__(self):
        return repr(self.message)

class InsertError(Exception):
    def __init__(self, table, message):
        self.table = table
        self.message = message

    def __str__(self):
        return repr(self.message)


class CommonError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
