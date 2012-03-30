#!/usr/bin/env python
#coding=utf-8
"""
    views: account.py
    ~~~~~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
from datetime import datetime
import cPickle as pickle

from pypress.views.base import RequestHandler
from pypress.database import db
from pypress.models import User, UserCode
from pypress.extensions.routing import route

@route(r'/login', name='login')
class Login(RequestHandler):
    def get(self):
        
        form = self.forms.LoginForm(next=self.get_args('next'))

        self.render('account/login.html', form=form)
        return

    def post(self):

        form = self.forms.LoginForm(self.request.arguments)

        if form.validate():
            user, authenticated = User.query.authenticate(self.get_args('login',''), 
                                                          self.get_args('password',''))
            if user and authenticated:

                user.last_login = datetime.utcnow() # utcnow
                db.session.commit()

                # set cookie
                self.session['user'] = user
                # self.session.set_expires(days=2)
                self.session.save()

                # flash
                self.flash(self._("Welcome back, %s" % user.username), "success")

                # redirect
                next_url = form.next.data
                if not next_url:
                    next_url = '/'
                self.redirect(next_url)
                return
            else:
                form.submit.errors.append(self._("The username or password you provided are incorrect."))
        
        self.render('account/login.html', form=form)
        return


@route(r'/logout', name='logout')
class Logout(RequestHandler):
    def get(self):
        
        del self.session["user"]
        self.session.save()
        
        # redirect
        next_url = self.get_args('next')
        if not next_url:
            next_url = '/'
        self.redirect(next_url)
        return


@route(r'/signup', name='signup')
class Signup(RequestHandler):
    def get(self):
        
        form = self.forms.SignupForm(next=self.get_args('next'))
        
        self.render("account/signup.html", form=form)
        return

    def post(self):
        
        form = self.forms.SignupForm(self.request.arguments)

        if form.validate():

            code = UserCode.query.filter_by(code=form.code.data).first()
    
            if code:
                user = User(role=code.role)
                form.populate_obj(user)

                db.session.add(user)
                db.session.delete(code)
                db.session.commit()
                
                self.session['user'] = user

                next_url = form.next.data

                if not next_url:
                    next_url = self.reverse_url('people', user.username)

                return self.redirect(next_url)
            else:
                form.code.errors.append(self._("Code is not allowed"))
        
        self.render("account/signup.html", form=form)
        return


@route(r'/i18n', name='language')
class Language(RequestHandler):
    def get(self):
        code = self.get_args('lang','en_US')
        self.set_cookie('lang', code)
        
        next_url = self.get_args('next','/')
        self.redirect(next_url)
        return


