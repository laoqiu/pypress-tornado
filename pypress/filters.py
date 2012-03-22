#!/usr/bin/env python
#coding=utf-8

import tornado.template


def field_errors(field):
    t = tornado.template.Template("""
        {% if field.errors %}
        <ul class="errors">
            {% for error in field.errors %}
            <li>{{ error }}</li>
            {% end %}
        </ul>
        {% end %}
        """)
    return t.generate(field=field)

