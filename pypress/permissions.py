#! /usr/bin/env python
#coding=utf-8
"""
    permissions.py
    ~~~~~~~~~~~
    set role need permissions
    :author: laoqiu.com@gmail.com
"""

from extensions.permission import RoleNeed, Permission

admin = Permission(RoleNeed('admin'))
moderator = Permission(RoleNeed('moderator'))
auth = Permission(RoleNeed('authenticated'))

