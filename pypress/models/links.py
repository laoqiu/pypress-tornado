#!/usr/bin/env python
#coding=utf-8
"""
    models: links.py
    ~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
from datetime import datetime

from pypress.extensions.cache import cached_property
from pypress.helpers import storage
from pypress.database import db


__all__ = ['Link',]
   
class Link(db.Model):

    __tablename__ = "links"

    PER_PAGE = 80

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)
    link = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(100))
    description = db.Column(db.Unicode(100))
    email = db.Column(db.String(50))
    passed = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    class Permissions(object):
        
        def __init__(self, obj):
            self.obj = obj


    def __init__(self, *args, **kwargs):
        super(Link, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return "<%s>" % self
    
    @cached_property
    def permissions(self):
        return self.Permissions(self)

    @cached_property
    def json(self):
        return dict(id=self.id,
                    name=self.name,
                    url=self.link,
                    logo=self.logo,
                    description=self.description,
                    created_date=self.created_date)
    
    @cached_property
    def item(self):
        return storage(self.json)
