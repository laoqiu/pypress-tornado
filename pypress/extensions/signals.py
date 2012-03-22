
#!/usr/bin/env python
#coding=utf-8
"""
    signals.py
    ~~~~~~~~~~~~~
    
    Implements signals based on blinker if available, otherwise
    falls silently back to a noop

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
try:
    from blinker import Namespace
except ImportError:
    class Namespace(object):
        def signal(self, name, doc=None):
            return _FakeSignal(name, doc)

    class _FakeSignal(object):
        """If blinker is unavailable, create a fake class with the same
        interface that allows sending of signals but will fail with an
        error on anything else.  Instead of doing anything on send, it
        will just ignore the arguments and do nothing instead.
        """

        def __init__(self, name, doc=None):
            self.name = name
            self.__doc__ = doc

        def _fail(self, *args, **kwargs):
            raise RuntimeError('signalling support is unavailable '
                               'because the blinker library is '
                               'not installed.')

        send = lambda *args, **kwargs: None

        connect = disconnect = has_receivers_for = receivers_for = \
            temporarily_connected_to = connected_to = _fail

        del _fail


# _signals = Namespace()

# comment_saved = _signals.signal('comment-saved')

