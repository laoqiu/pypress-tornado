#!/usr/bin/env python
#coding=utf-8
"""
    extensions.session
    ~~~~~~~~
    :origin version in https://gist.github.com/1735032
"""
try:
    import cPickle as pickle
except ImportError:
    import pickle
from uuid import uuid4


class RedisSessionStore(object):

    def __init__(self, redis_connection, **options):
        self.options = {
            'key_prefix': 'session',
            'expire': 7200,
        }
        self.options.update(options)
        self.redis = redis_connection

    def prefixed(self, sid):
        return '%s:%s' % (self.options['key_prefix'], sid)

    def generate_sid(self, ):
        return uuid4().get_hex()

    def get_session(self, sid):
        data = self.redis.hget(self.prefixed(sid), 'data')
        session = pickle.loads(data) if data else dict()
        return session

    def set_session(self, sid, session_data):
        self.redis.hset(self.prefixed(sid), 'data', pickle.dumps(session_data))
        expiry = self.options['expire']
        if expiry:
            self.redis.expire(self.prefixed(sid), expiry)

    def delete_session(self, sid):
        self.redis.delete(self.prefixed(sid))


class Session(object):

    def __init__(self, session_store, session_id=None):
        self._store = session_store
        self._sid = session_id if session_id else self._store.generate_sid()
        self._data = self._store.get_session(self._sid)
        self._dirty = False

    def clear(self):
        self._store.delete_session(self._sid)

    @property
    def id(self):
        return self._sid

    def __getattr__(self, key):
        return self._data[key]

    def __setattr__(self, key, value):
        self._data[key] = value
        self._dirty = True

    def __delattr__(self, key):
        del self._data[key]
        self._dirty = True

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        for key in self._data:
            yield key

    def __repr__(self):
        return self._data.__repr__()

    def __del__(self):
        if self._dirty:
            self._save()

    def _save(self):
        self._store.set_session(self._sid, self._data)
        self._dirty = False


