#!/usr/bin/env python
#coding=utf-8
"""
    forms.py
    ~~~~~~~~~~~~~
    wtforms extensions for tornado
"""
import re

from tornado.escape import _unicode

from wtforms import Form as BaseForm, fields, validators, widgets, ext

from wtforms.fields import BooleanField, DecimalField, DateField, \
    DateTimeField, FieldList, FloatField, FormField, \
    HiddenField, IntegerField, PasswordField, RadioField, SelectField, \
    SelectMultipleField, SubmitField, TextField, TextAreaField

from wtforms.validators import ValidationError, Email, email, EqualTo, equal_to, \
    IPAddress, ip_address, Length, length, NumberRange, number_range, \
    Optional, optional, Required, required, Regexp, regexp, \
    URL, url, AnyOf, any_of, NoneOf, none_of

from wtforms.widgets import CheckboxInput, FileInput, HiddenInput, \
    ListWidget, PasswordInput, RadioInput, Select, SubmitInput, \
    TableWidget, TextArea, TextInput

try:
    import sqlalchemy
    _is_sqlalchemy = True
except ImportError:
    _is_sqlalchemy = False


if _is_sqlalchemy:
    from wtforms.ext.sqlalchemy.fields import QuerySelectField, \
        QuerySelectMultipleField

    for field in (QuerySelectField, 
                  QuerySelectMultipleField):

        setattr(fields, field.__name__, field)


class Form(BaseForm):
    """
    Example:
    >>> user = User.query.get(1)
    >>> form = LoginForm(user)
    {{ xsrf_form_html }}
    {{ form.hiden_tag() }}
    {{ form.username }}
    """

    def __init__(self, formdata=None, *args, **kwargs):
        self.obj = kwargs.get('obj', None)
        super(Form, self).__init__(formdata, *args, **kwargs)
    
    def process(self, formdata=None, *args, **kwargs):
        if formdata is not None and not hasattr(formdata, 'getlist'):
            formdata = TornadoInputWrapper(formdata)
        super(Form, self).process(formdata, *args, **kwargs)
    
    def hidden_tag(self, *fields):
        """
        Wraps hidden fields in a hidden DIV tag, in order to keep XHTML 
        compliance.
        """

        if not fields:
            fields = [f for f in self if isinstance(f, HiddenField)]

        rv = []
        for field in fields:
            if isinstance(field, basestring):
                field = getattr(self, field)
            rv.append(unicode(field))

        return u"".join(rv)
    
    
class TornadoInputWrapper(dict):
    """
    From tornado source-> RequestHandler.get_arguments
    """
    def getlist(self, name, strip=True):
        values = []
        for v in self.get(name, []):
            v = _unicode(v)
            if isinstance(v, unicode):
                # Get rid of any weird control chars (unless decoding gave
                # us bytes, in which case leave it alone)
                v = re.sub(r"[\x00-\x08\x0e-\x1f]", " ", v)
            if strip:
                v = v.strip()
            values.append(v)
        return values
        
        
