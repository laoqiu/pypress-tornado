#!/usr/bin/env python
#coding=utf-8

import tornado.web

class Post(tornado.web.UIModule):
    def render(self, post, show_comments=False):
        return self.render_string(
            "blog/module-post.html", post=post, show_comments=show_comments)


class Comment(tornado.web.UIModule):
    def render(self, comment, form):
        return self.render_string("blog/module-comment.html", comment=comment, form=form)

