#!/usr/bin/env python
#coding=utf-8
"""
    views: links.py
    ~~~~~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
import urllib
import tornado.web

from pypress.views.base import RequestHandler
from pypress.database import db
from pypress.models import Link
from pypress.extensions.routing import route
from pypress.permissions import admin


@route(r'/links', name='links')
class Links(RequestHandler):
    def get(self):
        
        page = self.get_args('page', 1, type=int)
        
        page_obj = Link.query.paginate(page=page, per_page=Link.PER_PAGE)

        page_url = lambda page: self.reverse_url('links') + \
                            '?%s' % urllib.urlencode(dict(page=page))

        self.render("links/list.html",
                    page_obj=page_obj,
                    page_url=page_url)
        return


@route(r'/link/add', name='link_add')
class Add(RequestHandler):
    @tornado.web.authenticated
    @admin.require(401)
    def post(self):

        url = self.get_args('url')
        name = self.get_args('name')
        email = self.get_args('email')
        logo = self.get_args('logo')
        description = self.get_args('description')
        
        if url and name:
            link = Link(name=name, 
                        link=url,
                        email=email,
                        logo=logo,
                        description=description,
                        passed=True)

            db.session.add(link)
            db.session.commit()
            
            next_url = self.get_args('next', self.reverse_url('links'))
        else:
            next_url = self.request.uri

        self.redirect(next_url)
        return


@route(r'/link/(\d+)/delete', name='link_delete')
class Delete(RequestHandler):
    @tornado.web.authenticated
    @admin.require(401)
    def post(self, id):

        link = Link.query.get_or_404(int(id))
        
        db.session.delete(link)
        
        next_url = self.get_args('next', self.reverse_url('links'))
        self.redirect(next_url)
        return


