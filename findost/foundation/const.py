#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'LexusLee'
"""
模拟提供一个const变量
"""


class Const:
    """
    用法：
        from common import Const
        Const.url = "http://www.int-long.com"
    """
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            raise self.ConstError, "Can't rebind const (%s)" % name
        self.__dict__[name] = value

    def __getattr__(self, item):
        return self.__dict__[item] if item in self.__dict__.keys() else None



import sys
sys.modules[__name__] = Const()

if __name__ == '__main__':
    print 'Test begin.'

    print 'Test end.'