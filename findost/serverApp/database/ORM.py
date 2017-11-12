# -*- coding:utf-8 -*-
__author__ = 'lidongchao'

"""
数据库ORM模块
"""

from tornado import gen

from foundation.log import logger
from serverApp.common.connectionPool import dbpool

_triggers = frozenset(['pre_insert', 'pre_update', 'pre_insert'])


# 所有数据库支持类型的基类，可以根据数据库类型进行扩充
class Field(object):
    _count = 0

    def __init__(self, **kw):
        self.name = kw.get('name', None)
        self._default = kw.get('default', None)
        self.nullable = kw.get('nullable', False)
        self.primary_key = kw.get('primary_key', False)
        self._order = Field._count
        Field._count = Field._count + 1
        self.ddl = kw.get('ddl', '')

    @property
    def default(self):
        d = self._default
        return d() if callable(d) else d

    def __str__(self):
        s = ['<%s:%s,%s,default(%s),' % (self.__class__.__name__, self.name, self.ddl, self._default)]
        self.nullable and s.append('N')
        s.append('>')
        return ''.join(s)

# groupby order limit count
class Expr(object):
    def __init__(self, model, kwargs, operator):
        self.model = model
        self.params = kwargs.values()
        self.group = []
        #equations = [key + ' = %s' for key in kwargs.keys()]
        equations = []
        for item in kwargs.iteritems():
            if isinstance(item[1], tuple):
                equations.append(item[0] + ' in %s')
            else:
                equations.append(item[0] + ' = %s')
        if operator == 'and':
            self.where_expr = 'where ' + ' and '.join(equations) if len(equations) > 0 else ''
        elif operator == 'or':
            self.where_expr = 'where ' + ' or '.join(equations) if len(equations) > 0 else ''


    def limit(self, rows, offset=None):
        """
        限制返回的记录条数
        :param rows:        int 记录条数
        :param offset:      int 偏移量
        :return:
        """
        if isinstance(rows, int):
            self.where_expr += '%s%s' % (
                ' limit %s' % rows if rows > -1 else '',
                ' offset %s' % offset if offset and isinstance(offset, int) else '')
        return self

    def order(self, key, is_asc=True):
        """
        对数据进行排序
        :param key:         str 排序字段
        :param is_asc:      bool 升序或者降序
        :return:
        """
        if key is None or key not in self.model.__mappings__:
            return self
        if 'order by' in self.where_expr:
            self.where_expr += ', %s %s' % (key, 'asc' if is_asc else 'desc')
        else:
            self.where_expr += ' order by %s %s' % (key, 'asc' if is_asc else 'desc')
        return self

    def returning(self, single_row, *args):
        for i, k in enumerate(args):
            if k not in self.model.__mappings__:
                continue
            if i == 0 and single_row:
                self.where_expr += ' returning %s' % (args[i])
            elif i == 0 and not single_row:
                self.where_expr += ' returnings %s' % (args[i])
            else:
                self.where_expr += ', %s' % (args[i])
        return self

    def groupby(self, *args):
        for i, k in enumerate(args):
            if k not in self.model.__mappings__:
                continue
            if i == 0:
                self.where_expr += ' group by %s' % (args[i])
            else:
                self.where_expr += ', %s' % (args[i])
            self.group.append(args[i])
        return self

    @gen.coroutine
    def select(self, size, *args, **kwargs):
        _keys = []
        if len(args) == 0:
            _keys = self.model.__mappings__.keys()
        else:
            for key in args:
                if key not in self.model.__mappings__:
                    continue
                _keys.append(key)
        if 'distinct' in kwargs and kwargs['distinct']:
            sql = 'select distinct %s from %s %s;' % (
                ', '.join(_keys), self.model.__name__, self.where_expr)
        else:
            sql = 'select %s from %s %s;' % (
                ', '.join(_keys), self.model.__name__, self.where_expr)
        rs = yield _db.select(sql, size, *self.params)
        if rs is None or len(rs) == 0:
            raise gen.Return(None)
        raise gen.Return(rs)

    @gen.coroutine
    def update(self, **kwargs):
        """
        更新操作，**kwargs接收字典变量，如自增需添加add_itself为字典key，且将自增字段添加为value，如add_itself=('id', 'num')
        :param kwargs:      dict:参数
        :return:            返回影响行数，执行失败为0，或返回dict，包含相应的字段名，没有返回None
        """
        _keys = []
        _params = []
        add_itself_items = ()
        add_itself_sql = ''
        # 处理 set a=a+5
        if 'add_itself' in kwargs:
            add_itself_items = kwargs['add_itself']
            if not isinstance(add_itself_items, tuple):
                add_itself_items = (add_itself_items,)
            for add_itself_item in add_itself_items:
                if add_itself_item in self.model.__mappings__:
                    if add_itself_sql != '':
                        add_itself_sql += ','
                    add_itself_sql += add_itself_item + ' = ' + add_itself_item + ' + %s ' % kwargs[add_itself_item]
                    # print add_itself_sql
        for key, val in kwargs.iteritems():
            if val is None or key not in self.model.__mappings__ or key in add_itself_items:
                continue
            _keys.append(key)
            _params.append(val)
        _params.extend(self.params)
        if not _keys and not add_itself_sql:
            raise gen.Return(1)
        sql = 'update %s set %s %s %s;' % (
            self.model.__name__,
            ', '.join([key + ' = %s' for key in _keys]) if _keys else '',
            ', ' + add_itself_sql if _keys and add_itself_sql else add_itself_sql,
            self.where_expr)
        rc = yield _db.execute(sql, *_params)
        raise gen.Return(rc)

    @gen.coroutine
    def delete(self):
        sql = 'delete from %s %s;' % (
            self.model.__name__, self.where_expr)
        rs = yield _db.execute(sql, *self.params)
        if rs is None:
            raise gen.Return(None)
        raise gen.Return(rs)

    @gen.coroutine
    def count(self, *args):
        selection = ','.join(args) + ',' if args else ''
        if not self.group:
            sql = 'select %s count(*) from %s %s;' % (selection, self.model.__name__, self.where_expr)
        else:
            join = ','.join(self.group)
            sql = 'select %s %s, count(*) from %s %s;' % (selection, join, self.model.__name__, self.where_expr)
        row_cnt = yield _db.select(sql, -1, *self.params)
        raise gen.Return(row_cnt)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        mappings = dict()
        primary_key = None
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                if not v.name:
                    v.name = k
                if v.primary_key:
                    if primary_key:
                        raise TypeError('Cannot define more than one primary key in class: %s' % name)
                    if v.nullable:
                        v.nullable = False
                    primary_key = v
                mappings[k] = v
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' % name)
        for k in mappings.iterkeys():
            attrs.pop(k)
        attrs['__table__'] = name.lower()
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primary_key
        for trigger in _triggers:
            if not trigger in attrs:
                attrs[trigger] = None
        return type.__new__(cls, name, bases, attrs)


class Model(dict):
    __metaclass__ = ModelMetaclass

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    @gen.coroutine
    def get(cls, pk):
        d = yield _db.select('select * from %s where %s = %s' % (cls.__table__, cls.__primary_key__.name, '%s'), 1, pk)
        raise gen.Return(cls(**d)) if d else gen.Return(None)

    @classmethod
    def where(cls, **kwargs):
        return Expr(cls, kwargs, 'and')

    @classmethod
    def whereor(cls, **kwargs):
        return Expr(cls, kwargs, 'or')

    @gen.coroutine
    def insert(self, *returning):
        params = {}
        returns = []
        for item in returning:
            if item in self.__mappings__:
                returns.append(item)
        for k, v in self.__mappings__.iteritems():
            if k not in self or getattr(self, k) is None:
                continue
            params[v.name] = getattr(self, k)
        val = params.values()
        sql = "insert into %s(%s) values (%s) %s;" % (
            self.__table__,
            ", ".join(params.keys()),
            ", ".join(["%s" for i in params.values()]),
            " returning %s " % ", ".join(returns) if returns else " "
        )
        res = yield _db.execute(sql, *val)
        raise gen.Return(res)



class DB:

    @gen.coroutine
    def execute(self, sql, *args):
        """
        执行操作
        :param sql:         str:sql语句
        :param args:        tuple:参数
        :return:            返回影响行数，执行失败为0，或返回dict，包含相应的字段名，没有返回None
        """
        if sql.lower().find("returnings") != -1:
            sql = sql.lower().replace('returnings', 'returning')
            getid = 2
        elif sql.lower().find("returning") != -1:
            getid = 1
        else:
            getid = 0
        execute_sql = yield dbpool.mogrify(sql, args)
        logger.debug(execute_sql)
        cursor = yield dbpool.execute(sql, args or ())
        if getid == 0:
            raise gen.Return(cursor.rowcount)
        elif getid == 2:
            item = cursor.fetchall()
            raise gen.Return(item)
        else:
            item = cursor.fetchone()
            raise gen.Return(item)

    @gen.coroutine
    def select(self, sql, size, *args):
        """
        查询操作
        :param sql:             str:待执行的sql语句
        :param size:            int:返回查询后的数据条数，负数表示查询所有
        :param args:            tuple:sql参数
        :return:                size=1:返回dict，如果无结果返回None
                                size!=1:返回list,每个list是一个dict，如果无结果返回[]
        """
        execute_sql = yield dbpool.mogrify(sql, args)
        logger.debug(execute_sql)
        cursor = yield dbpool.execute(sql, args or ())
        if size == 1:
            rs = cursor.fetchone()
            raise gen.Return(rs)
        elif size > 1:
            rs = cursor.fetchmany(size)
            raise gen.Return(rs)
        else:
            rs = cursor.fetchall()
            raise gen.Return(rs)


    def _param_db_mapping(self, db_param, param_dict):
        """
        将参数转化为数据中的字段,同时过滤掉不合法的参数
        :param db_param:
        :param param_dict:
        :return:
        """
        copy_param_dict = dict(param_dict)
        for param in copy_param_dict.keys():
            if param in db_param:
                copy_param_dict[db_param[param]] = copy_param_dict.pop(param)
            else:
                copy_param_dict.pop(param)
        return copy_param_dict

_db = DB()