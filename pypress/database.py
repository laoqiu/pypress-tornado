#!/usr/bin/env python
#coding=utf-8
import settings

from extensions.sqlalchemy import SQLAlchemy, BaseQuery, \
        models_committed, before_models_committed

db = SQLAlchemy(settings.SQLALCHEMY_DATABASE_URI, settings.SQLALCHEMY_DATABASE_ECHO)

