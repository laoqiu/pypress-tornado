#!/usr/bin/env python
#coding=utf-8
"""
    extensions: permission.py
    permission for tornado. from flask-principal.
    :modified by laoqiu.com@gmail.com

    Example:
    >>> from extensions.permission import UserNeed, RoleNeed, ItemNeed, Permission
    >>> admin = Permission(RoleNeed('admin'))
    >>> editor = Permission(UserNeed(1)) & admin

    # handers
    ~~~~~~~~~

    @admin.require(401)
    def get(self):
        self.write('is admin')
        return
     
    def post(self):
        # or
        if editor.can(self.identity):
            print 'admin'
        # or
        editor.test(self.identity, 401)
        return

"""
import sys
import tornado.web

from functools import wraps, partial
from collections import namedtuple

__all__ = ['UserNeed', 'RoleNeed', 'ItemNeed', 'Permission', 'Identity', 'AnonymousIdentity']

Need = namedtuple('Need', ['method', 'value'])

UserNeed = partial(Need, 'user')
RoleNeed = partial(Need, 'role')
ItemNeed = namedtuple('ItemNeed', ['method', 'value', 'type'])


class PermissionDenied(RuntimeError):
    """Permission denied to the resource"""
    pass


class Identity(object):
    """
    A set of needs provided by this user
    
    example:
        identity = Identity('ali')
        identity.provides.add(('role', 'admin'))
    """
    def __init__(self, name):
        self.name = name
        self.provides = set()

    def can(self, permission):
        return permission.allows(self)


class AnonymousIdentity(Identity):
    """An anonymous identity
    :attr name: "anonymous"
    """
    def __init__(self):
        Identity.__init__(self, 'anonymous')


class IdentityContext(object):
    """The context of an identity for a permission.

    .. note:: The principal is usually created by the flaskext.Permission.require method
              call for normal use-cases.

    The principal behaves as either a context manager or a decorator. The
    permission is checked for provision in the identity, and if available the
    flow is continued (context manager) or the function is executed (decorator).
    """

    def __init__(self, permission, http_exception=None, identity=None):
        self.permission = permission
        self.http_exception = http_exception
        self.identity = identity if identity else AnonymousIdentity()

    def can(self):
        """Whether the identity has access to the permission
        """
        return self.identity.can(self.permission)

    def __call__(self, method):
        @wraps(method)
        def wrapper(handler, *args, **kwargs):
            self.identity = handler.identity
            self.__enter__()
            exc = (None, None, None)
            try:
                result = method(handler, *args, **kwargs)
            except Exception:
                exc = sys.exc_info()
            self.__exit__(*exc)
            return result
        return wrapper
    
    def __enter__(self):
        # check the permission here
        if not self.can():
            if self.http_exception:
                raise tornado.web.HTTPError(self.http_exception)
            raise PermissionDenied(self.permission)

    def __exit__(self, *exc):
        if exc != (None, None, None):
            cls, val, tb = exc
            raise cls, val, tb
        return False


class Permission(object):
    """
    Represents needs, any of which must be present to access a resource
    :param needs: The needs for this permission
    """
    def __init__(self, *needs):
        self.needs = set(needs)
        self.excludes = set()

    def __and__(self, other):
        """Does the same thing as "self.union(other)"
        """
        return self.union(other)
    
    def __or__(self, other):
        """Does the same thing as "self.difference(other)"
        """
        return self.difference(other)

    def __contains__(self, other):
        """Does the same thing as "other.issubset(self)".
        """
        return other.issubset(self)
    
    def require(self, http_exception=None, identity=None):
        return IdentityContext(self, http_exception, identity)
        
    def test(self, identity, http_exception=None):
        with self.require(http_exception, identity):
            pass
        
    def reverse(self):
        """
        Returns reverse of current state (needs->excludes, excludes->needs) 
        """

        p = Permission()
        p.needs.update(self.excludes)
        p.excludes.update(self.needs)
        return p

    def union(self, other):
        """Create a new permission with the requirements of the union of this
        and other.

        :param other: The other permission
        """
        p = Permission(*self.needs.union(other.needs))
        p.excludes.update(self.excludes.union(other.excludes))
        return p

    def difference(self, other):
        """Create a new permission consisting of requirements in this 
        permission and not in the other.
        """

        p = Permission(*self.needs.difference(other.needs))
        p.excludes.update(self.excludes.difference(other.excludes))
        return p

    def issubset(self, other):
        """Whether this permission needs are a subset of another

        :param other: The other permission
        """
        return self.needs.issubset(other.needs) and \
               self.excludes.issubset(other.excludes)

    def allows(self, identity):
        """Whether the identity can access this permission.

        :param identity: The identity
        """
        if self.needs and not self.needs.intersection(identity.provides):
            return False

        if self.excludes and self.excludes.intersection(identity.provides):
            return False

        return True
    
    def can(self, identity):
        """Whether the required context for this permission has access

        This creates an identity context and tests whether it can access this
        permission
        """
        return self.require(identity=identity).can()


