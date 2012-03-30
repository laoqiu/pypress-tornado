#!/usr/bin/env python
#coding=utf-8
"""
    pypress Application
    ~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
import os
import redis

import tornado.web
import tornado.locale

from tornado.web import url

from pypress import settings as config
from pypress import uimodules
from pypress.helpers import setting_from_object
from pypress.forms import create_forms
from pypress.views import account, blog, links, ErrorHandler
from pypress.database import db, models_committed
from pypress.extensions.routing import Route
from pypress.extensions.sessions import RedisSessionStore

class Application(tornado.web.Application):
    def __init__(self):
        settings = setting_from_object(config)
        handlers = [
            # other handlers...
            url(r"/theme/(.+)", tornado.web.StaticFileHandler, dict(path=settings['theme_path']), name='theme_path'),
            url(r"/upload/(.+)", tornado.web.StaticFileHandler, dict(path=settings['upload_path']), name='upload_path')
        ] + Route.routes()
        
        # Custom 404 ErrorHandler
        handlers.append((r"/(.*)", ErrorHandler)) 
        
        settings.update(dict(
            ui_modules = uimodules,
            autoescape = None
        ))
        
        if 'default_locale' in settings:
            tornado.locale.load_gettext_translations(
                os.path.join(os.path.dirname(__file__), 'translations'), 'messages')

        tornado.web.Application.__init__(self, handlers, **settings)
        
        self.forms = create_forms()
        self.redis = redis.StrictRedis()
        self.session_store = RedisSessionStore(self.redis)
        
        configure_signals(db.sender)
    
        
def configure_signals(sender):
    
    @models_committed.connect_via(sender)
    def on_models_commited(sender, changes):
        # print sender
        pass


