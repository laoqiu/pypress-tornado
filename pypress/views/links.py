#!/usr/bin/env python
#coding=utf-8
"""
    views: links.py
    ~~~~~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
import urllib
import tornado.web

from pypress.views import RequestHandler
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
    def get(self):

        form = self.forms.LinkForm()

        self.render("links/add.html", form=form)
        return 

    def post(self):
        
        form = self.forms.LinkForm(self.request.arguments)

        if form.validate():
            
            link = Link()
            form.populate_obj(link)

            db.session.add(link)
            db.session.commit()

            self.flash("Waiting for passed...")
            
            next_url = self.get_args('next', self.reverse_url('links'))
            self.redirect(next_url)

        self.render("links/add.html", form=form)
        return


@route(r'/link/(\d+)/pass', name='link_pass')
class Pass(RequestHandler):
    @tornado.web.authenticated
    @admin.require(401)
    def get(self, id):

        link = Link.query.get_or_404(int(id))
        
        link.passed = True

        next_url = self.get_args('next', self.reverse_url('links'))
        self.redirect(next_url)
        return


@route(r'/link/(\d+)/delete', name='link_delete')
class Delete(RequestHandler):
    @tornado.web.authenticated
    @admin.require(401)
    def get(self, id):

        link = Link.query.get_or_404(int(id))
        
        db.session.delete(link)
        db.session.commit()
        
        next_url = self.get_args('next', self.reverse_url('links'))
        self.redirect(next_url)
        return


