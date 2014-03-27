import sys
import datetime
import re
import deform
import colander
import itertools
import jinja2
from deform import ValidationFailure
from deform.widget import CheckedPasswordWidget
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.encode import urlencode
from pyramid.response import Response

from kotti import get_settings
from mba import _

class FormCustom(deform.Form):
    def __init__(self, schema, **kw):
        super(FormCustom, self).__init__(schema, **kw)
        template = kw.pop('template', None)
        if template:
            self.widget.template = template
        readonly_template = kw.pop('readonly_template', None)
        if readonly_template:
            self.widget.readonly_template = readonly_template

