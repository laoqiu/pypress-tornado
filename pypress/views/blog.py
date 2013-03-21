#!/usr/bin/env python
#coding=utf-8
"""
    views: blog.py
    ~~~~~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
import json
import os
import urllib
import logging
import tornado.web
import tornado.escape

from datetime import datetime

from pypress.views import RequestHandler
from pypress.database import db
from pypress.models import User, Post, Tag, Comment
from pypress.helpers import generate_random
from pypress.utils.imagelib import Recaptcha
from pypress.extensions.routing import route


@route(r'/', name='archive')
@route(r'/(\d{4})/', name='archive_year')
@route(r'/(\d{4})/(\d{1,2})/', name='archive_month')
@route(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', name='archive_day')
class Archive(RequestHandler):
    def get(self, year=None, month=None, day=None):
        
        page = self.get_args('page', 1, type=int)
        
        page_obj = Post.query.archive(year, month, day).as_list() \
                             .paginate(page=page, per_page=Post.PER_PAGE)
        
        if day:
            path = self.reverse_url('archive_day', year, month, day)
        elif month:
            path = self.reverse_url('archive_month', year, month)
        elif year:
            path = self.reverse_url('archive_year', year)
        else:
            path = self.reverse_url('archive')

        page_url = lambda page: path + \
                            '?%s' % urllib.urlencode(dict(page=page))

        self.render("blog/list.html", 
                    page_obj=page_obj,
                    page_url=page_url)
        return


@route(r'/archives', name='archives')
class Archives(RequestHandler):
    def get(self):
        
        page = self.get_args('page', 1, type=int)
        
        page_obj = Post.query.as_list() \
                             .paginate(page=page, per_page=Post.PER_PAGE)

        page_url = lambda page: self.reverse_url('archives') + \
                            '?%s' % urllib.urlencode(dict(page=page))

        self.render("blog/archives.html",
                    page_obj=page_obj,
                    page_url=page_url)
        return


@route(r'/search', name='search')
class Search(RequestHandler):
    def get(self):
        
        keywords = self.get_args('q')
        page = self.get_args('page', 1, type=int)

        if not keywords:
            self.redirect('/')
            return

        page_obj = Post.query.search(keywords).as_list() \
                             .paginate(page, per_page=Post.PER_PAGE)

        if page_obj.total == 1:
            post = page_obj.items[0]
            self.redirect(post.url)
            return
            
        page_url = lambda page: self.reverse_url('search') + \
                                '?%s' % urllib.urlencode(dict(page=page,
                                                              q=keywords))
                                                        
        self.render("blog/search.html", 
                    page_obj=page_obj,
                    page_url=page_url,
                    keywords=keywords)
        return


@route(r'/tags', name='tags')
class TagWall(RequestHandler):
    def get(self):
        
        tags = Tag.query.cloud()

        self.render("blog/tags.html", tags=tags)
        return


@route(r'/tag/(.+)', name='tag')
class TagView(RequestHandler):
    def get(self, slug):
        
        page = self.get_args('page', 1, type=int)

        tag = Tag.query.filter_by(slug=slug).first_or_404()

        page_obj = tag.posts.as_list() \
                            .paginate(page, per_page=Post.PER_PAGE)

        page_url = lambda page: self.reverse_url('tag', slug) + \
                                '?%s' % urllib.urlencode(dict(page=page))
        
        self.render("blog/tag.html",
                    page_obj=page_obj,
                    page_url=page_url,
                    tagname=tag.name)
        return 


@route(r'/people/(.+)', name='people')
class People(RequestHandler):
    def get(self, username):
        
        page = self.get_args('page', 1, type=int)
        
        people = User.query.get_by_username(username)
    
        page_obj = Post.query.filter(Post.author_id==people.id).as_list() \
                             .paginate(page, per_page=Post.PER_PAGE)
    
        page_url = lambda page: self.reverse_url('people', username) + \
                                '?%s' % urllib.urlencode(dict(page=page))
    
        self.render("blog/people.html", 
                    page_obj=page_obj,
                    page_url=page_url,
                    people=people)
        return     


@route(r'/(\d{4})/(\d{1,2})/(\d{1,2})/(.+)', name='post_view')
class View(RequestHandler):
    def get(self, year, month, day, slug):
        
        post = Post.query.get_by_slug(slug)

        date = (post.created_date.year, 
                post.created_date.month, 
                post.created_date.day)

        if (int(year), int(month), int(day)) != date:
            raise tornado.web.HTTPError(404)

        self.render("blog/view.html", post=post, form=self.forms.CommentForm())
        return

    def post(self, year, month, day, slug):
        """ add comment """
         
        post = Post.query.get_by_slug(slug)

        form = self.forms.CommentForm(self.request.arguments)
        
        if form.validate():
            
            captcha = form.captcha.data

            if self.get_secure_cookie("captcha") == captcha:

                comment = Comment(post=post,
                                  ip=self.request.remote_ip)
                
                form.populate_obj(comment)
                
                if self.current_user:
                    comment.author_id = self.current_user.id

                db.session.add(comment)
                db.session.commit()

                self.redirect(comment.url)
                return

            form.captcha.errors.append(self._("Captcha don't match"))

        self.render("blog/view.html", post=post, form=form)
        return


@route(r'/post', name='post')
class Submit(RequestHandler):
    @tornado.web.authenticated
    def get(self):
        
        form = self.forms.PostForm(next=self.get_args('next',''))

        self.render("blog/post.html", form=form)
        return

    @tornado.web.authenticated
    def post(self):
        
        form = self.forms.PostForm(self.request.arguments)

        if form.validate():
            
            post = Post(author_id=self.current_user.id)
            form.populate_obj(post)

            db.session.add(post)
            db.session.commit()
            
            # redirect
            next_url = form.next.data
            if not next_url:
                next_url = post.url
            self.redirect(next_url)
            return

        self.render("blog/post.html", form=form)
        return 


@route(r'/post/(\d+)/edit', name='post_edit')
class Edit(RequestHandler):
    @tornado.web.authenticated
    def get(self, post_id):
     
        post = Post.query.get_or_404(post_id)

        post.permissions.edit.test(self.identity, 401)
    
        form = self.forms.PostForm(title = post.title,
                                   slug = post.slug,
                                   content = post.content,
                                   tags = post.tags,
                                   obj = post)
            
        self.render("blog/edit.html", form=form)
        return

    @tornado.web.authenticated
    def post(self, post_id):
        
        post = Post.query.get_or_404(post_id)
        
        post.permissions.edit.test(self.identity, 401)

        form = self.forms.PostForm(self.request.arguments, obj=post)
        
        if form.validate():
    
            form.populate_obj(post)
            db.session.commit()
    
            next_url = post.url
            self.redirect(next_url)
            return
    
        self.render("blog/edit.html", form=form)
        return


@route(r'/post/(\d+)/delete', name='post_delete')
class Delete(RequestHandler):
    @tornado.web.authenticated
    def get(self, post_id):
        
        post = Post.query.get_or_404(post_id)
        
        post.permissions.delete.test(self.identity, 401)

        db.session.delete(post)
        db.session.commit()

        self.redirect('/')
        return 


@route(r'/comment/(\d+)/delete', name='comment_delete')
class DeleteComment(RequestHandler):
    @tornado.web.authenticated
    def post(self, comment_id):
        
        comment = Comment.query.get_or_404(int(comment_id))

        comment.permissions.delete.test(self.identity, 401)

        db.session.delete(comment)
        db.session.commit()

        self.write(dict(success=True,
                        comment_id=comment_id))
        return


@route(r'/upload', name='upload')
class Upload(RequestHandler):
    def post(self):
        if 'upload' in self.request.files:
            f = self.request.files['upload'][0]

            if 'image' in f['content_type']:
                now = datetime.now()
                alt, ext = os.path.splitext(f['filename'])
                filename = now.strftime('%d%H%M%S%f') + ext
                dirs = os.path.join(self.settings['upload_path'], str(now.year), str(now.month))
                if not os.path.isdir(dirs):
                    os.makedirs(dirs)
                path = os.path.join(dirs, filename)
                try:
                    outfile = open(path, 'w')
                    outfile.write(f['body'])
                    outfile.close()
                except:
                    logging.debug("upload error")
                    error = "save file error"
                else:
                    filename = os.path.join('/upload', str(now.year), str(now.month), filename)
                    self.write(json.dumps(dict(success=True, result=dict(path=filename,alt=alt))))
                    # self.write(dict(success=True, result=dict(path=filename,alt=alt)))
                    return
            else:
                error = "file not image"
        else:
            error = "upload not in request.files"

        self.write(dict(success=False, error=error))
        return


@route(r'/captcha/get', name='get_captcha')
class GetCaptcha(RequestHandler):
    def get(self):
        text = generate_random(4)
        self.set_secure_cookie("captcha", text)
        
        strIO = Recaptcha(text)

        #,mimetype='image/png'
        self.set_header("Content-Type", "image/png")
        self.write(strIO.read())
        return


@route(r'/captcha/check', name='check_captcha')
class CheckCaptcha(RequestHandler):
    def get(self):
    
        captcha = self.get_args('captcha')
        
        if self.get_secure_cookie("captcha") == captcha:
            success = True
        else:
            success = False
        
        self.write(dict(success=success))
        return
    


