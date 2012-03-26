#!/usr/bin/env python
#coding=utf-8

import tornado.web

class Post(tornado.web.UIModule):
    def render(self, post, show_comments=False):
        return self.render_string(
            "blog/module-post.html", post=post, show_comments=show_comments)

class List(tornado.web.UIModule):
    def render(self, page_obj, page_url, *args):
        return self.render_string(
            "blog/module-list.html", page_obj=page_obj, page_url=page_url, *args)

class Comment(tornado.web.UIModule):
    def render(self, comment, form):
        return self.render_string("blog/module-comment.html", comment=comment, form=form)

class Paginate(tornado.web.UIModule):
    def render(self, page_obj, page_url, *args):
        return self.render_string(
            "macros/_page.html", page_obj=page_obj, page_url=page_url, *args)
