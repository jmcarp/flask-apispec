# -*- coding: utf-8 -*-

import six
import flask.views

from flask_smore import ResourceMeta

class MethodResourceMeta(ResourceMeta, flask.views.MethodViewType):
    pass

class MethodResource(six.with_metaclass(MethodResourceMeta, flask.views.MethodView)):
    """Subclass of `MethodView` that uses the `ResourceMeta` metaclass. Behaves
    exactly like `MethodView` but inherits **flask-smore** annotations.
    """
    methods = None
