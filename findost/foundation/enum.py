#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'LexusLee'
"""
构造枚举类
"""


class Enum:
    """
    枚举类
    """
    def __setattr__(self, key, value):
        if key in self.__dict__.keys():
            raise AttributeError("don't allow to set attribute.")
        self.__dict__[key] = value

    def __delattr__(self, item):
        raise AttributeError("don't allow to delete attribute.")


if __name__ == '__main__':
    print 'Test begin.'

    print 'Test end.'