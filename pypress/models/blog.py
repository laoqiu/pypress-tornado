#!/usr/bin/env python
#coding=utf-8
"""
    models: blog.py
    ~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""

import re, random
from datetime import datetime

import tornado.web

from pypress.extensions.sqlalchemy import BaseQuery
from pypress.extensions.cache import cached_property, cache
from pypress.extensions.routing import route
from pypress.extensions.permission import Permission, UserNeed
from pypress.helpers import storage, slugify, markdown, endtags
from pypress.permissions import admin, moderator
from pypress.database import db
from pypress.models.users import User


__all__ = ['Post', 'Tag', 'Comment']


class PostQuery(BaseQuery):

    def jsonify(self):
        for post in self.all():
            yield post.json

    def as_list(self):
        """
        Return restricted list of columns for list queries
        """

        deferred_cols = ("content", 
                         "tags",
                         "author.email",
                         "author.activation_key",
                         "author.date_joined",
                         "author.last_login")

        options = [db.defer(col) for col in deferred_cols]
        return self.options(*options)
    
    def get_by_slug(self, slug):
        post = self.filter(Post.slug==slug).first()
        if post is None:
            raise tornado.web.HTTPError(404)
        return post
    
    def search(self, keywords):

        criteria = []

        for keyword in keywords.split():
            keyword = '%' + keyword + '%'
            criteria.append(db.or_(Post.title.ilike(keyword),
                                   Post.content.ilike(keyword),
                                   Post.tags.ilike(keyword)
                                   ))

        q = reduce(db.and_, criteria)
        return self.filter(q)

    def archive(self, year, month, day):
        if not year:
            return self
        
        criteria = []
        criteria.append(db.extract('year',Post.created_date)==int(year))
        if month: criteria.append(db.extract('month',Post.created_date)==int(month))
        if day: criteria.append(db.extract('day',Post.created_date)==int(day))
        
        q = reduce(db.and_, criteria)
        return self.filter(q)


class Post(db.Model):

    __tablename__ = 'posts'

    PER_PAGE = 40    
    
    query_class = PostQuery
    
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, 
                          db.ForeignKey(User.id, ondelete='CASCADE'), 
                          nullable=False)
    
    _title = db.Column("title", db.Unicode(100), index=True)
    _slug = db.Column("slug", db.Unicode(50), unique=True, index=True)
    content = db.Column(db.UnicodeText)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    _tags = db.Column("tags", db.Unicode(100), index=True)

    author = db.relation(User, innerjoin=True, lazy="joined")

    __mapper_args__ = {'order_by': id.desc()}
        
    class Permissions(object):
        
        def __init__(self, obj):
            self.obj = obj
        
        @cached_property
        def edit(self):
            return Permission(UserNeed(self.obj.author_id))
    
        @cached_property
        def delete(self):
            return Permission(UserNeed(self.obj.author_id))

  
    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.title
    
    def __repr__(self):
        return "<%s>" % self
    
    @cached_property
    def permissions(self):
        return self.Permissions(self)

    def _get_title(self):
        return self._title

    def _set_title(self, title):
        self._title = title.lower().strip()
        if self.slug is None:
            self.slug = slugify(title)[:50]

    title = db.synonym("_title", descriptor=property(_get_title, _set_title))
    
    def _get_slug(self):
        return self._slug

    def _set_slug(self, slug):
        if slug:
            self._slug = slugify(slug)

    slug = db.synonym("_slug", descriptor=property(_get_slug, _set_slug))
    
    def _get_tags(self):
        return self._tags 

    def _set_tags(self, tags):
        
        self._tags = tags

        if self.id:
            # ensure existing tag references are removed
            d = db.delete(post_tags, post_tags.c.post_id==self.id)
            db.engine.execute(d)

        for tag in set(self.taglist):

            slug = slugify(tag)

            tag_obj = Tag.query.filter(Tag.slug==slug).first()
            if tag_obj is None:
                tag_obj = Tag(name=tag, slug=slug)
                db.session.add(tag_obj)
            
            tag_obj.posts.append(self)

    tags = db.synonym("_tags", descriptor=property(_get_tags, _set_tags))
    
    @cached_property
    def url(self):
        return route.url_for('post_view',
                    self.created_date.year, 
                    self.created_date.month,
                    self.created_date.day,
                    self.slug.encode('utf8'))

    @cached_property
    def taglist(self):
        if self.tags is None:
            return []

        tags = [t.strip() for t in self.tags.split(",")]
        return [t for t in tags if t]

    @cached_property
    def linked_taglist(self):
        return [(tag, route.url_for('tag', slugify(tag))) \
                    for tag in self.taglist]
    
    @cached_property
    def prev_post(self):
        prev_post = Post.query.filter(Post.created_date < self.created_date) \
                              .first()
        return prev_post

    @cached_property
    def next_post(self):
        next_post = Post.query.filter(Post.created_date > self.created_date) \
                              .order_by('created_date').first()
        return next_post

    @cached_property
    def summary(self):
        s = re.findall(r'(<hr>)', self.content)
        if not s:
            return self.content
        p = s[0]
        return endtags(self.content.split(p)[0])
    
    @property
    def comments(self):
        """
        Returns comments in tree. Each parent comment has a "comments" 
        attribute appended and a "depth" attribute.
        """
        comments = Comment.query.filter(Comment.post_id==self.id).all()

        def _get_comments(parent, depth):
            
            parent.comments = []
            parent.depth = depth

            for comment in comments:
                if comment.parent_id == parent.id:
                    parent.comments.append(comment)
                    _get_comments(comment, depth + 1)

        parents = [c for c in comments if c.parent_id is None]

        for parent in parents:
            _get_comments(parent, 0)

        return parents

    @cached_property
    def json(self):
        return dict(id=self.id,
                    title=self.title,
                    content=self.content,
                    author=self.author.username)
     

post_tags = db.Table("post_tags", db.Model.metadata,
    db.Column("post_id", db.Integer, 
              db.ForeignKey('posts.id', ondelete='CASCADE'), 
              primary_key=True),
    db.Column("tag_id", db.Integer, 
              db.ForeignKey('tags.id', ondelete='CASCADE'),
              primary_key=True))


class TagQuery(BaseQuery):
    
    @cache.cached(3600)
    def cloud(self):

        tags = self.filter(Tag.num_posts > 0).all()

        if not tags:
            return []

        max_posts = max(t.num_posts for t in tags)
        min_posts = min(t.num_posts for t in tags)

        diff = (max_posts - min_posts) / 10.0
        if diff < 0.1:
            diff = 0.1

        for tag in tags:
            tag.size = int(tag.num_posts / diff)
            if tag.size < 1: 
                tag.size = 1

        random.shuffle(tags)

        return tags
    

class Tag(db.Model):

    __tablename__ = "tags"
    
    query_class = TagQuery

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.Unicode(80), unique=True)
    posts = db.dynamic_loader(Post, secondary=post_tags, query_class=PostQuery)

    _name = db.Column("name", db.Unicode(80), unique=True)
    
    def __init__(self, *args, **kwargs):
        super(Tag, self).__init__(*args, **kwargs)
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s>" % self
    
    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name.lower().strip()
        self.slug = slugify(name)

    name = db.synonym("_name", descriptor=property(_get_name, _set_name))
    
    @cached_property
    def url(self):
        return route.url_for('tag', self.slug)

    num_posts = db.column_property(
        db.select([db.func.count(post_tags.c.post_id)]).\
            where(db.and_(post_tags.c.tag_id==id,
                          Post.id==post_tags.c.post_id)).as_scalar())


class CommentQuery(BaseQuery):

    def as_data(self):

        comments = [storage({'author':comment.author,
                     'parent':comment.parent,
                     'comment':comment.comment,
                     }) for comment in self.all()]

        return comments
    

class Comment(db.Model):

    __tablename__ = "comments"
    
    query_class = CommentQuery

    PER_PAGE = 40    
    
    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(db.Integer, 
                        db.ForeignKey(Post.id, ondelete='CASCADE'), 
                        nullable=False)

    author_id = db.Column(db.Integer, 
                          db.ForeignKey(User.id, ondelete='CASCADE')) 

    parent_id = db.Column(db.Integer, 
                          db.ForeignKey("comments.id", ondelete='CASCADE'))
    
    email = db.Column(db.String(50))
    nickname = db.Column(db.Unicode(50))
    website = db.Column(db.String(100))

    comment = db.Column(db.UnicodeText)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    ip = db.Column(db.String(20))

    _author = db.relation(User, backref="posts", lazy="joined")

    post = db.relation(Post, innerjoin=True, lazy="joined")

    parent = db.relation('Comment', lazy="joined", remote_side=[id])

    __mapper_args__ = {'order_by' : id.asc()}
    
    
    class Permissions(object):
        
        def __init__(self, obj):
            self.obj = obj
        
        @cached_property
        def edit(self):
            return Permission(UserNeed(self.obj.author_id))
    
        @cached_property
        def reply(self):
            return Permission(UserNeed(self.obj.post.author_id))

        @cached_property
        def delete(self):
            return admin & moderator

        
    def __init__(self, *args, **kwargs):
        super(Comment, self).__init__(*args, **kwargs)
    
    def __str__(self):
        return self.comment
    
    def __repr__(self):
        return "<%s>" % self

    @cached_property
    def permissions(self):
        return self.Permissions(self)
    
    def _get_author(self):
        if self._author:
            self._author.website = None
            return self._author
        return storage(email = self.email, 
                       nickname = self.nickname, 
                       website = self.website)

    def _set_author(self, author):
        self._author = author

    author = db.synonym("_author", descriptor=property(_get_author, _set_author))
    
    @cached_property
    def url(self):
        return "%s#comment-%s" % (self.post.url, self.id)

    @cached_property
    def markdown(self):
        return markdown(self.comment or '')
    
    @cached_property
    def json(self):
        return dict(id=self.id,
                    author=self.author,
                    url=self.url,
                    comment=self.comment,
                    created_date=self.created_date)
    
    @cached_property
    def item(self):
        return storage(self.json)
   

Post.num_comments = db.column_property(
            db.select([db.func.count(Comment.post_id)]) \
                    .where(Comment.post_id==Post.id).as_scalar(), deferred=True)


