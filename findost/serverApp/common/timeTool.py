# -*- coding:utf-8 -*-
import datetime
class timetool():
    @classmethod
    def get_now_time(cls,time_template='%Y-%m-%d %H:%M:%S'):
        return datetime.datetime.now().strftime(time_template)
    def get_now_day(cls,time_template="%Y%m%d"):
        return datetime.datetime.now().strftime(time_template)