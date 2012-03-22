#!/usr/bin/env python
#coding=utf-8

import uuid

import tornado.httpserver
import tornado.ioloop
import tornado.options

from tornado.options import define, options 

from pypress import Application
from pypress.models import *
from pypress.database import db

define("cmd", default='runserver', 
        metavar="runserver|createall|dropall|createcode",
        help=("Default use runserver"))
define("port", default=9000, help="default: 9000, required runserver", type=int)
define("num", default=1, help="number of create codes. required createcode", type=int)
define("role", default='admin', metavar="admin|moderator|member", help="required createcode")

def main():
    tornado.options.parse_command_line()

    if options.cmd == 'runserver':
        print 'server started. port %s' % options.port
        http_server = tornado.httpserver.HTTPServer(Application())
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()

    elif options.cmd == 'createall':
        "Creates database tables"
        db.create_all()
        print 'create all [ok]'

    elif options.cmd == 'dropall':
        "Drops all database tables"
        db.drop_all()
        print 'drop all [ok]'

    elif options.cmd == 'createcode':
        codes = []
        usercodes = []
        for i in range(options.num):
            code = unicode(uuid.uuid4()).split('-')[0]
            codes.append(code)
            usercode = UserCode()
            usercode.code = code
            if options.role == "admin":
                usercode.role = User.ADMIN
            elif options.role == "moderator":
                usercode.role = User.MODERATOR
            else:
                usercode.role = User.MEMBER
            usercodes.append(usercode)
        if options.num==1:
            db.session.add(usercode)
        else:
            db.session.add_all(usercodes)
        db.session.commit()
        print "Sign up code:"
        for i in codes:
            print i

    else:
        print 'error cmd param: python manager.py --help'

if __name__=='__main__':
    main()

