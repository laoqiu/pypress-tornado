#!/usr/bin/env python
#coding=utf-8
import os

DEBUG = True
COOKIE_SECRET = 'simple'
LOGIN_URL = '/login'
XSRF_COOKIES = True

#TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')

THEME_PATH = os.path.join(os.path.dirname(__file__), 'themes')
THEME_NAME = 'default'

UPLOAD_PATH = os.path.join(os.path.dirname(__file__), 'uploads')

DEFAULT_LOCALE = 'en_US' #'zh_CN'

try:
    from local_settings import *
except:
    pass

