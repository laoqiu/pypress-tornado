#!/usr/bin/env python
#coding=utf-8
"""
    helpers.py
    ~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
import re
import markdown
import functools
import hashlib
import random

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
_pre_re = re.compile(r'<pre (?=lang=[\'"]?\w+[\'"]?).*?>(?P<code>[\w\W]+?)</pre>')
_lang_re = re.compile(r'lang=[\'"]?(?P<lang>\w+)[\'"]?')


class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
    >>> o = storage(a=1)
    >>> o.a
    1
    >>> o['a']
    1
    >>> o.a = 2
    >>> o['a']
    2
    >>> del o.a
    >>> o.a
    Traceback (most recent call last):
    ...
    AttributeError: 'a'
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'


class Gravatar(object):
    """
    Simple object for create gravatar link.

    gravatar = Gravatar(
    size=100,
    rating='g',
    default='retro',
    force_default=False,
    force_lower=False
    )

    :param app: Your Flask app instance
    :param size: Default size for avatar
    :param rating: Default rating
    :param default: Default type for unregistred emails
    :param force_default: Build only default avatars
    :param force_lower: Make email.lower() before build link

    From flask-gravatar http://packages.python.org/Flask-Gravatar/

    """
    def __init__(self, size=100, rating='g', default='mm',
                 force_default=False, force_lower=False):

        self.size = size
        self.rating = rating
        self.default = default
        self.force_default = force_default

    def __call__(self, email, size=None, rating=None, default=None,
                 force_default=None, force_lower=False):

        """Build gravatar link."""

        if size is None:
            size = self.size

        if rating is None:
            rating = self.rating

        if default is None:
            default = self.default

        if force_default is None:
            force_default = self.force_default

        if force_lower is None:
            force_lower = self.force_lower

        if force_lower:
            email = email.lower()

        hash = hashlib.md5(email).hexdigest()

        link = 'http://www.gravatar.com/avatar/{hash}'\
               '?s={size}&d={default}&r={rating}'.format(**locals())

        if force_default:
            link = link + '&f=y'

        return link


def setting_from_object(obj):
    settings = dict()
    for key in dir(obj):
        if key.isupper():
            settings[key.lower()] = getattr(obj, key)
    return settings


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug. From http://flask.pocoo.org/snippets/5/"""
    result = []
    for word in _punct_re.split(text.lower()):
        #word = word.encode('translit/long')
        if word:
            result.append(word)
    return unicode(delim.join(result))


def generate_random(length=8):
    """Generate random number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def endtags(html):
    """ close all open html tags at the end of the string """

    NON_CLOSING_TAGS = ['AREA', 'BASE', 'BASEFONT', 'BR', 'COL', 'FRAME',
            'HR', 'IMG', 'INPUT', 'ISINDEX', 'LINK', 'META', 'PARAM']

    opened_tags = re.findall(r"<([a-z]+)[^<>]*>",html)
    closed_tags = re.findall(r"</([a-z]+)>",html)

    opened_tags = [i.lower() for i in opened_tags if i.upper() not in NON_CLOSING_TAGS]
    closed_tags = [i.lower() for i in closed_tags]

    len_opened = len(opened_tags)

    if len_opened==len(closed_tags):
        return html

    opened_tags.reverse()

    for tag in opened_tags:
        if tag in closed_tags:
            closed_tags.remove(tag)
        else:
            html += "</%s>" % tag
     
    return html


def gistcode(content):
    result = list(set(re.findall(r"(<a[^<>]*>\s*(https://gist.github.com/\d+)\s*</a>)", content)))
    for i,link in result:
        content = content.replace(i, '%s <script src="%s.js"></script>' % (i, link))
    return content


def code_highlight(value):
    f_list = _pre_re.findall(value)

    if f_list:
        s_list = _pre_re.split(value)

        for code_block in _pre_re.finditer(value):

            lang = _lang_re.search(code_block.group()).group('lang')
            code = code_block.group('code')

            index = s_list.index(code)
            s_list[index] = code2html(code, lang)

        return u''.join(s_list)

    return value
    

def code2html(code, lang):
    lexer = get_lexer_by_name(lang, stripall=True)
    formatter = HtmlFormatter()
    return highlight(code, lexer, formatter)


markdown = functools.partial(markdown.markdown,
                             safe_mode='remove',
                             output_format="html")

storage = Storage
gravatar = Gravatar()

