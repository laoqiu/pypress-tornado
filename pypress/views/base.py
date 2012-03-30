#!/usr/bin/env python
#coding=utf-8
"""
    views: base.py
    ~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
import os

import logging
import tornado.web
import tornado.locale
import tornado.escape
import tornado.ioloop

from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import HtmlFormatter

from pypress.database import db
from pypress.models import Comment, Tag, Link
from pypress.extensions.permission import Identity, AnonymousIdentity
from pypress.extensions.cache import cache
from pypress.extensions.sessions import RedisSession, Session


class FlashMessageMixIn(object):
    """
        Store a message between requests which the user needs to see.

        views
        -------

        self.flash("Welcome back, %s" % username, 'success')

        base.html
        ------------
        
        {% set messages = handler.get_flashed_messages() %}
        {% if messages %}
        <div id="flashed">
            {% for category, msg in messages %}
            <span class="flash-{{ category }}">{{ msg }}</span>
            {% end %}
        </div>
        {% end %}
    """
    def flash(self, message, category='message'):
        messages = self.messages()
        messages.append((category, message))
        self.set_secure_cookie('flash_messages', tornado.escape.json_encode(messages))
    
    def messages(self):
        messages = self.get_secure_cookie('flash_messages')
        messages = tornado.escape.json_decode(messages) if messages else []
        return messages
        
    def get_flashed_messages(self):
        messages = self.messages()
        self.clear_cookie('flash_messages')
        return messages
    

class PermissionMixIn(object):
    @property
    def identity(self):
        if not hasattr(self, "_identity"):
            self._identity = self.get_identity()
        return self._identity

    def get_identity(self):
        if self.current_user:
            identity = Identity(self.current_user.id)
            identity.provides.update(self.current_user.provides)
            return identity
        return AnonymousIdentity()


class CachedItemsMixIn(object):
    def get_cached_items(self, name):
        items = cache.get(name)
        if items is None:
            items = self.set_cached_items(name)
        return items

    def set_cached_items(self, name, limit=10):
        items = []
        if name == 'latest_comments':
            items = [comment.item for comment in Comment.query.order_by(Comment.created_date.desc()).limit(limit)]
        elif name == 'tags':
            items = Tag.query.cloud()
        elif name == 'links':
            items = [link.item for link in Link.query.filter(Link.passed==True).limit(limit)]
        cache.set(name, items)
        return items


class RequestHandler(tornado.web.RequestHandler, PermissionMixIn, FlashMessageMixIn, CachedItemsMixIn):
    def on_finish(self):
        """sqlalchemy connection close. 
        fixed sqlalchemy error: 'Can't reconnect until invalid'. new in version 2.2"""
        db.session.remove()

    def get_current_user(self):
        user = self.session['user'] if 'user' in self.session else None
        return user
    
    @property
    def session(self):
        if hasattr(self, '_session'):
            return self._session
        else:
            self.require_setting('permanent_session_lifetime', 'session')
            expires = self.settings['permanent_session_lifetime'] or None
            if 'redis_server' in self.settings and self.settings['redis_server']:
                sessionid = self.get_secure_cookie('sid')
                self._session = RedisSession(self.application.session_store, sessionid, expires_days=expires)
                if not sessionid: 
                    self.set_secure_cookie('sid', self._session.id, expires_days=expires)
            else:
                self._session = Session(self.get_secure_cookie, self.set_secure_cookie, expires_days=expires)
            return self._session
    
    def get_user_locale(self):
        code = self.get_cookie('lang', self.settings.get('default_locale', 'zh_CN'))
        return tornado.locale.get(code)
    
    def get_template_path(self):
        if 'theme_path' in self.settings:
            return os.path.join(self.settings['theme_path'], self.settings.get('theme_name', 'default'), 'templates')
        return self.settings.get('template_path')
    
    def get_error_html(self, status_code, **kwargs):
        if self.settings.get('debug', False) is False:
            self.set_status(status_code)
            return self.render_string('errors/%s.html' % status_code)

        else:
            def get_snippet(fp, target_line, num_lines):
                if fp.endswith('.html'):
                    fp = os.path.join(self.get_template_path(), fp)

                half_lines = (num_lines/2)
                try:
                    with open(fp) as f:
                        all_lines = [line for line in f]
                        code = ''.join(all_lines[target_line-half_lines-1:target_line+half_lines])
                        formatter = HtmlFormatter(linenos=True, linenostart=target_line-half_lines, hl_lines=[half_lines+1])
                        lexer = get_lexer_for_filename(fp) 
                        return highlight(code, lexer, formatter)
                
                except Exception, ex:
                    logging.error(ex)
                    return ''

            css = HtmlFormatter().get_style_defs('.highlight')
            exception = kwargs.get('exception', None)
            return self.render_string('errors/exception.htm', 
                                      get_snippet=get_snippet,
                                      css=css,
                                      exception=exception,
                                      status_code=status_code, 
                                      kwargs=kwargs)
    
    def get_args(self, key, default=None, type=None):
        if type==list:
            if default is None: default = []
            return self.get_arguments(key, default)
        value = self.get_argument(key, default)
        if value and type:
            try:
                value = type(value)
            except ValueError:
                value = default
        return value
    
    @property
    def is_xhr(self):
        '''True if the request was triggered via a JavaScript XMLHttpRequest.
        This only works with libraries that support the `X-Requested-With`
        header and set it to "XMLHttpRequest".  Libraries that do that are
        prototype, jQuery and Mochikit and probably some more.'''
        return self.request.headers.get('X-Requested-With', '') \
                           .lower() == 'xmlhttprequest'
    
    @property
    def forms(self):
        return self.application.forms[self.locale.code]

    def _(self, message, plural_message=None, count=None):
        return self.locale.translate(message, plural_message, count)

 
class ErrorHandler(RequestHandler):
    """raise 404 error if url is not found.
    fixed tornado.web.RequestHandler HTTPError bug.
    """
    def prepare(self):
        self.set_status(404)
        raise tornado.web.HTTPError(404)


