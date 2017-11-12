# -*- coding:utf-8 -*-
__author__ = 'LexusLee'

import time
import json

import tornado
import tornado.gen

from tornado.web import HTTPError

from tornado.escape import json_decode

from foundation.log import logger
from foundation import const
from serverAppConfig import DEVICE_TYPE
from serverAppConfig import TOKEN_ROLE, TOKEN_DEADLINE_TIME, TOKEN_USER_ID
from cacheTool import _get_redis_connection


class ArgumentTypeError(HTTPError):
    """Exception raised by `IntLongRequestHandler.add_query_argument`.

    This is a subclass of `HTTPError`, so if it is uncaught a 400 response
    code will be used instead of 500 (and a stack trace will not be logged).
    """
    def __init__(self, arg_name):
        super(ArgumentTypeError, self).__init__(
            400, 'Type of argument %s must be string type' % arg_name)
        self.arg_name = arg_name


class RequestHandlerAha(tornado.web.RequestHandler):
    """
　  根据需要，定制tornado.web.RequestHandler
    """
    def __init__(self, application, request, auto_init=True, **kwargs):
        """
        构造函数
        :param write_to_client: 如果是后台调用，该值必须是True,否则是False，默认为False
        """
        super(RequestHandlerAha, self).__init__(application, request, **kwargs)

        self.auto_init = auto_init
        self.decoded_secure_cookie = {}
        self.redis_client = None

    def on_finish(self):
        if self.redis_client:
            logger.debug('存在redis连接，所以关闭连接')
            self.redis_client.disconnect()

    def get_secure_cookie(self, name, value=None, max_age_days=31,
                          min_version=None):
        """
        重写重写tornado.web.RequestHandler中的get_secure_cookie方法，用于在多次调用get_secure_cookie
        不重复去解密
        :param name:
        :return:
        """
        if name in self.decoded_secure_cookie.keys():
            return self.decoded_secure_cookie[name]
        else:
            value = super(RequestHandlerAha, self).get_secure_cookie(name, value, max_age_days, min_version)
            self.decoded_secure_cookie[name] = value
            return value

    def get_current_user_role(self):
        """
        返回当前用户的角色名字,角色名字参考configueFiles文件夹下面的authority文件注释
        :return: 角色名字
        """
        tokenstr = self.get_secure_cookie("token")
        if not tokenstr:
            logger.debug("cookie中没有token,因此是游客访问")
            return "visitor"
        token = json_decode(tokenstr)
        role = token.get(TOKEN_ROLE, "visitor")
        return role

    def get_current_user(self):
        """
        重写tornado.web.RequestHandler中的get_current_user方法，用于在调用self.current_user能正确返回
        直接调用该函数可以返回相应的用户id,也可以使用self.current_user来返回用户的id。
        :return: 如果有相应的token，则返回对应的id，否则返回None
        """
        tokenstr = self.get_secure_cookie("token")
        if not tokenstr:
            logger.debug("cookie中没有token,因此是游客访问,因此没有用户的id")
            return None
        token = json_decode(tokenstr)
        user_id = token.get(TOKEN_USER_ID)
        return user_id

    def write(self, chunk):
        """
        向调用者返回数据，如果是客户端直接请求的，则向客户端返回对应写的数据，函数返回None；如果是后台自己调用，
        则返回相应的python对象数据，函数返回对应python对象数据
        :param chunk: 待返回的数据
        :return: 如果是后台自己调用，返回对应数据的python对象；否则返回None
        """
        # self.set_header("Content-Type", "application/json; charset=UTF-8")
        if self.auto_init:
            super(RequestHandlerAha, self).write(chunk)
        else:
            return chunk

    def __add_arg(self, source, name, *args):
        """
        用来底层实现增加请求参数
        :param source: 增加参数到指定的source上
        :param name: 参数的名字，必须是字符串
        :param args: 参数的值，可以是多个参数，但是必须是字符串
        :return:None
        :exception ArgumentTypeError
        """
        if not isinstance(name, basestring):
            raise ArgumentTypeError(name)
        for v in args:
            if not isinstance(v, basestring):
                raise ArgumentTypeError(name)

        addvalue = list(args)
        if name in self.request.query_arguments.keys():
            addvalue.extend(source.get(name, []))

        self.request.query_arguments[name] = addvalue

    def add_query_argument(self, name, *args):
        """
        增加query的参数，形如URL后面的参数
        :param name: 参数的名字，必须是字符串
        :param args: 参数的值，可以是多个参数，但是必须是字符串
        :return:None
        """
        self.__add_arg(self.request.query_arguments, name, *args)

    def add_body_argument(self, name, *args):
        """
        增加body的参数，形如提交表单里面的数据
        :param name: 参数的名字，必须是字符串
        :param args: 参数的值，可以是多个参数，但是必须是字符串
        :return:None
        """
        self.__add_arg(self.request.body_arguments, name, *args)

    def add_argument(self, name, *args):
        """
        增加全局参数
        :param name: 参数的名字，必须是字符串
        :param args: 参数的值，可以是多个参数，但是必须是字符串
        :return:None
        """
        self.__add_arg(self.request.arguments, name, *args)

    def get_redis_conn(self):
        """
        得到一个redis的连接
        """
        if not self.redis_client:
            self.redis_client = _get_redis_connection()
            return self.redis_client

    @property
    def device_type(self):
        """
        得到设备类型，返回的模拟枚举类型: DEVICE_TYPE
        :return:
        """
        if not hasattr(self, "_device_type"):
            userAgent = self.request.headers.get('User-Agent', "")
            via = self.request.headers.get("Via", "")
            self._device_type = self._distinguishDevice(via, userAgent)
        return self._device_type

    def _distinguishDevice(self, via, userAgent):
        """
        验证设备是什么类型设备
        :param via:
        :param userAgent:
        :return: 0代表手机，1表示pc
        """
        pcHeaders = ["Windows 98",
                     "Windows ME",
                     "Windows 2000",
                     "Windows XP",
                     "Windows NT",
                     "Ubuntu"]

        mobileGateWayHeaders = [ "ZXWAP",
                                 "chinamobile.com",
                                 "monternet.com",
                                 "infoX",
                                 "wap.lizongbo.com","Bytemobile"]

        mobileUserAgents = [ "Nokia", "SAMSUNG", "MIDP-2", "CLDC1.1", "SymbianOS", "MAUI", "UNTRUSTED/1.0", "Windows CE",
                            "iPhone", "iPad", "Android", "BlackBerry", "UCWEB", "ucweb", "BREW", "J2ME", "YULONG",
                            "YuLong", "COOLPAD","TIANYU","TY-", "K-Touch",  "Haier", "DOPOD","Lenovo","LENOVO", "HUAQIN",
                            "AIGO-", "CTC/1.0", "CTC/2.0","CMCC","DAXIAN","MOT-","SonyEricsson","GIONEE","HTC","ZTE",
                            "HUAWEI",  "webOS","GoBrowser","IEMobile", "WAP2.0"]
        pcFlag = False
        mobileFlag = False
        for pcHeader in pcHeaders:
            if pcFlag:
                break
            if userAgent.find(pcHeader) != -1:
                pcFlag = True
            break
        for mobileGateWayHeader in mobileGateWayHeaders:
            if mobileFlag:
                break
            if via.find(mobileGateWayHeader) != -1:
                mobileFlag = True
                break

        for mobileUserAgent in mobileUserAgents:
            if mobileFlag:
                break
            if userAgent.find(mobileUserAgent) != -1:
                mobileFlag = True
                break

        if mobileFlag==True and mobileFlag!=pcFlag:
            return DEVICE_TYPE.MOBILE
        else:
            return DEVICE_TYPE.PC


class ResponseJSON:
    """
    处理返回给客户端的json对象
    """
    def __init__(self, code, data=None, description=None, status=None):
        """
        :param code: 返回的code，数字类型
        :param description: code相关描述
        :param data: 具体的data数据
        """
        self.code = code
        self.description = description
        self.data = data
        self.status = status

    def resultDict(self):
        """
        返回一个dict对象。如果code不是数字，则认为系统内部错误，code置为500。如果
        description为空，则没有description在dict中。如果data为一个json对象字符串，则会把对应
        的字符串转换成dict
        :return:返回一个dict对象
        """
        if isinstance(self.code, int):
            meta = {"code": self.code}
        else:
            meta = {"code": 500}

        if const.basic.get('send_description') == 'True' and self.description:
            meta["description"] = self.description

        if self.status:
            if isinstance(self.status, int):
                meta['status'] = self.status
            else:
                meta['status'] = -9999

        rdict = {"meta": meta}
        if isinstance(self.data, basestring):
            try:
                rdict["data"] = json.loads(self.data, encoding="utf-8")
            except ValueError:
                logger.warning("ResponseJSON:data数据格式错误")
        elif isinstance(self.data, dict) or isinstance(self.data, list):
            rdict["data"] = self.data

        return rdict

    def resultStr(self):
        """
        返回的是结果json字符串
        """
        return json.dumps(self.resultDict(), ensure_ascii=False)


def _auth_user_token(token):
    """
    通过token去验证用户是否已经登陆成功
    :param token:字典格式，token：
        CT: create_time,该token创建时间
        DT: deadline_time,该token的有效日期
    :return: 验证成功返回True，验证失败返回False
    """
    if token is None:
        return False
    else:
        token = json_decode(token)
        deadline_time = token[TOKEN_DEADLINE_TIME]
        now_time = get_system_time(pretty=False)
        if now_time < deadline_time:
            return True
        else:
            return False


def authenticated(method):
    """
    Decorate methods with this to require that the user be logged in.
    """
    def wrapper(self, *args, **kwargs):
        try:
            if not self.request.loginSuccess:    # 第一次登陆会产生异常，如果没有产生异常，说明已经验证过登陆了
                return self.write(ResponseJSON(401, description="not login.").resultDict())
                # return '已经验证过登陆，但是验证失败'
        except AttributeError:
            resp = _auth_user_token(self.get_secure_cookie("token"))
            if resp:
                self.request.loginSuccess = True
                return method(self, *args, **kwargs)
            else:
                self.request.loginSuccess = False
                return self.write(ResponseJSON(401, description="not login").resultDict())
                # return '验证失败'
        else:
            return method(self, *args, **kwargs)

    return wrapper


def _auth_user_authority(code, role):
    """
    通过code去验证用户是否有该权限
    :param code: 功能标识码
    :return: 如果验证成功，返回True，否则返回False
    """
    logger.debug(role)
    rolelist = const.authority.get(str(code))
    logger.debug(rolelist)
    if role in rolelist:
        return True
    else:
        return False


def authorized(code):
    """
    一个装饰器，用来验证该用户是否有权限使用该功能，如果有使用该模块的权限，则
    返回对应的函数，如果没有，则函数不继续往下执行
    :param code: 该模块的标识
    """
    def _deco(method):
        def wrappers(self, *args, **kwargs):
            role = self.get_current_user_role()
            resp = _auth_user_authority(code, role)
            if resp:
                return method(self, *args, **kwargs)
            else:
                logger.debug("该用户没有此功能的权限")
                return self.write(ResponseJSON(403, description="No authority for the function").resultDict())  # 该用户没有该权限
        return wrappers
    return _deco


def get_system_time(pretty=True):
    """
    该函数用于返回系统当前时间
    :return:当前系统时间
    """
    if pretty:
        ISOTIMEFORMAT = "%Y-%m-%d-%X"
        current_time =  time.strftime(ISOTIMEFORMAT, time.localtime(time.time()))
    else:
        current_time = time.time()
    return current_time
