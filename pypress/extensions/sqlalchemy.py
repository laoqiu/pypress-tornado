#!/usr/bin/env python
#coding=utf-8
"""
    sqlalchemy.py
    ~~~~~~~~~~~~~
    :copyright: (c) 2010 by Armin Ronacher. From flask-sqlalchemy.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement, absolute_import
import re
import uuid
from math import ceil
import functools
from functools import partial
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import attributes, object_mapper
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.orm.interfaces import MapperExtension, SessionExtension, \
     EXT_CONTINUE
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.util import to_list
from .signals import Namespace

import tornado.web

_camelcase_re = re.compile(r'([A-Z]+)(?=[a-z0-9])')
_signals = Namespace()

models_committed = _signals.signal('models-committed')
before_models_committed = _signals.signal('before-models-committed')


def _make_table(db):
    def _make_table(*args, **kwargs):
        if len(args) > 1 and isinstance(args[1], db.Column):
            args = (args[0], db.metadata) + args[1:]
        return sqlalchemy.Table(*args, **kwargs)
    return _make_table


def _set_default_query_class(d):
    if 'query_class' not in d:
        d['query_class'] = BaseQuery


def _wrap_with_default_query_class(fn):
    @functools.wraps(fn)
    def newfn(*args, **kwargs):
        _set_default_query_class(kwargs)
        if "backref" in kwargs:
            backref = kwargs['backref']
            if isinstance(backref, basestring):
                backref = (backref, {})
            _set_default_query_class(backref[1])
        return fn(*args, **kwargs)
    return newfn


def _defines_primary_key(d):
    """Figures out if the given dictonary defines a primary key column."""
    return any(v.primary_key for k, v in d.iteritems()
               if isinstance(v, sqlalchemy.Column))


def _include_sqlalchemy(obj):
    for module in sqlalchemy, sqlalchemy.orm:
        for key in module.__all__:
            if not hasattr(obj, key):
                setattr(obj, key, getattr(module, key))
    # Note: obj.Table does not attempt to be a SQLAlchemy Table class.
    obj.Table = _make_table(obj)
    obj.mapper = signalling_mapper
    obj.relationship = _wrap_with_default_query_class(obj.relationship)
    obj.relation = _wrap_with_default_query_class(obj.relation)
    obj.dynamic_loader = _wrap_with_default_query_class(obj.dynamic_loader)


class _BoundDeclarativeMeta(DeclarativeMeta):

    def __new__(cls, name, bases, d):
        tablename = d.get('__tablename__')

        # generate a table name automatically if it's missing and the
        # class dictionary declares a primary key.  We cannot always
        # attach a primary key to support model inheritance that does
        # not use joins.  We also don't want a table name if a whole
        # table is defined
        if not tablename and not d.get('__table__') and \
           _defines_primary_key(d):
            def _join(match):
                word = match.group()
                if len(word) > 1:
                    return ('_%s_%s' % (word[:-1], word[-1])).lower()
                return '_' + word.lower()
            d['__tablename__'] = _camelcase_re.sub(_join, name).lstrip('_')

        return DeclarativeMeta.__new__(cls, name, bases, d)

    def __init__(self, name, bases, d):
        bind_key = d.pop('__bind_key__', None)
        DeclarativeMeta.__init__(self, name, bases, d)
        if bind_key is not None:
            self.__table__.info['bind_key'] = bind_key


class _SignallingSession(Session):

    def __init__(self, db, autocommit=False, autoflush=False, **options):
        self.sender = db.sender
        self._model_changes = {}
        Session.__init__(self, autocommit=autocommit, autoflush=autoflush,
                         expire_on_commit=False,
                         extension=db.session_extensions,
                         bind=db.engine, **options)


class _QueryProperty(object):

    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, type):
        try:
            mapper = orm.class_mapper(type)
            if mapper:
                return type.query_class(mapper, session=self.sa.session())
        except UnmappedClassError:
            return None


class _SignalTrackingMapperExtension(MapperExtension):

    def after_delete(self, mapper, connection, instance):
        return self._record(mapper, instance, 'delete')

    def after_insert(self, mapper, connection, instance):
        return self._record(mapper, instance, 'insert')
    
    def after_update(self, mapper, connection, instance):
        return self._record(mapper, instance, 'update')

    def _record(self, mapper, model, operation):
        pk = tuple(mapper.primary_key_from_instance(model))
        #orm.object_session(model)._model_changes[pk] = (model, operation)
        changes = {}
        
        for prop in object_mapper(model).iterate_properties:
            if not isinstance(prop, RelationshipProperty):
                try:
                    history = attributes.get_history(model, prop.key)
                except:
                    continue

                added, unchanged, deleted = history

                newvalue = added[0] if added else None

                if operation=='delete':
                    oldvalue = unchanged[0] if unchanged else None
                else:
                    oldvalue = deleted[0] if deleted else None

                if newvalue or oldvalue:
                    changes[prop.key] = (oldvalue, newvalue)
        
        orm.object_session(model)._model_changes[pk] = (model.__tablename__, pk[0], changes, operation)
        return EXT_CONTINUE


class _SignallingSessionExtension(SessionExtension):

    def before_commit(self, session):
        d = session._model_changes
        if d:
            before_models_committed.send(session.sender, changes=d.values())
        return EXT_CONTINUE
    
    def after_commit(self, session):
        d = session._model_changes
        if d:
            models_committed.send(session.sender, changes=d.values())
            d.clear()
        return EXT_CONTINUE
    
    def after_rollback(self, session):
        session._model_changes.clear()
        return EXT_CONTINUE


def signalling_mapper(*args, **kwargs):
    """Replacement for mapper that injects some extra extensions"""
    extensions = to_list(kwargs.pop('extension', None), [])
    extensions.append(_SignalTrackingMapperExtension())
    kwargs['extension'] = extensions
    return sqlalchemy.orm.mapper(*args, **kwargs)


class _ModelTableNameDescriptor(object):

    def __get__(self, obj, type):
        tablename = type.__dict__.get('__tablename__')
        if not tablename:
            def _join(match):
                word = match.group()
                if len(word) > 1:
                    return ('_%s_%s' % (word[:-1], word[-1])).lower()
                return '_' + word.lower()
            tablename = _camelcase_re.sub(_join, type.__name__).lstrip('_')
            setattr(type, '__tablename__', tablename)
        return tablename


class Pagination(object):
    def __init__(self, query, page, per_page):
        self.query = query
        self.per_page = per_page
        self.page = page

    @property
    def total(self):
        return self.query.count()
    
    @property
    def items(self):
        return self.query.offset((self.page - 1) * self.per_page).limit(self.per_page)

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
        
    has_prev = property(lambda x: x.page > 1)
    prev_num = property(lambda x: x.page - 1)
    has_next = property(lambda x: x.page < x.pages)
    next_num = property(lambda x: x.page + 1)
    pages = property(lambda x: max(0, x.total - 1) // x.per_page + 1)


class BaseQuery(orm.Query):
    """The default query object used for models.  This can be subclassed and
    replaced for individual models by setting the :attr:`~Model.query_class`
    attribute.  This is a subclass of a standard SQLAlchemy
    :class:`~sqlalchemy.orm.query.Query` class and has all the methods of a
    standard query as well.
    """
    def get_or_404(self, ident):
        """Like :meth:`get` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.get(ident)
        if rv is None:
            raise tornado.web.HTTPError(404)
        return rv
    
    def first_or_404(self):
        """Like :meth:`first` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.first()
        if rv is None:
            raise tornado.web.HTTPError(404)
        return rv

    def paginate(self, page, per_page=20, error_out=True):
        """Returns `per_page` items from page `page`.  By default it will
        abort with 404 if no items were found and the page was larger than
        1.  This behavor can be disabled by setting `error_out` to `False`.

        Returns an :class:`Pagination` object.
        """
        if error_out and page < 1:
            raise tornado.web.HTTPError(404)
        return Pagination(self, page, per_page)


class Model(object):
    """Baseclass for custom user models."""

    #: the query class used.  The :attr:`query` attribute is an instance
    #: of this class.  By default a :class:`BaseQuery` is used.
    query_class = BaseQuery

    #: an instance of :attr:`query_class`.  Can be used to query the
    #: database for instances of this model.
    query = None
    
    PER_PAGE = None
    

class SQLAlchemy(object):
    """
    Example:
        db = SQLAlchemy("sqlite:///test.db", True)
        
        class User(db.Model):
            username = db.Column(db.String(16), unique=True, nullable=False, index=True)
            password = db.Column(db.String(30), nullable=False)
            email = db.Column(db.String(30), nullable=False)

        >>> user1 = User.query.filter(User.username=='name').first()
        >>> user2 = User.query.get(1)
        >>> user_list = User.query.filter(db.and_(User.username=='test1', User.email.ilike('%@gmail.com'))).limit(10)
        
    """
    def __init__(self, engine_url, echo=False, pool_recycle=7200, pool_size=10,
                 session_extensions=None, session_options=None):
        # create signals sender
        self.sender = str(uuid.uuid4())

        self.session_extensions = to_list(session_extensions, []) + \
                                  [_SignallingSessionExtension()]
        self.session = self.create_scoped_session(session_options)
        self.Model = self.make_declarative_base()
        
        self.engine = sqlalchemy.create_engine(engine_url, echo=echo, pool_recycle=pool_recycle, pool_size=pool_size)

        _include_sqlalchemy(self)

    def create_scoped_session(self, options=None):
        """Helper factory method that creates a scoped session."""
        if options is None:
            options = {}
        return orm.scoped_session(partial(_SignallingSession, self, **options))

    def make_declarative_base(self):
        """Creates the declarative base."""
        base = declarative_base(cls=Model, name='Model',
                                mapper=signalling_mapper,
                                metaclass=_BoundDeclarativeMeta)
        base.query = _QueryProperty(self)
        return base

    def create_all(self):
        """Creates all tables."""
        self.Model.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """Drops all tables."""
        self.Model.metadata.drop_all(bind=self.engine)

