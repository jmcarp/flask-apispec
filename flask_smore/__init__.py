# -*- coding: utf-8 -*-

__version__ = '0.1.0'

import copy
import types
import functools

import six
from six.moves import http_client as http

import flask
import werkzeug
from webargs import flaskparser

from flask_smore.utils import resolve_instance, resolve_annotations

def identity(value):
    return value

def unpack(resp):
    resp = resp if isinstance(resp, tuple) else (resp, )
    return resp + (None, ) * (3 - len(resp))

def activate(func):
    if getattr(func, '__meta__', {}).get('wrapped'):
        return func

    func.__args__ = getattr(func, '__args__', [])
    func.__schemas__ = getattr(func, '__schemas__', [])
    func.__meta__ = getattr(func, '__meta__', {})

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        config = flask.current_app.config
        parser = config.get('SMORE_WEBARGS_PARSER', flaskparser.parser)
        format_response = config.get('SMORE_FORMAT_RESPONSE', flask.jsonify) or identity

        obj = args[0] if func.__meta__.get('ismethod') else None
        __args__ = resolve_annotations(obj, getattr(func, '__args__'))
        __schemas__ = resolve_annotations(obj, getattr(func, '__schemas__'))
        if __args__.get('_apply', True):
            kwargs.update(parser.parse(__args__.get('args', {})))
        response = func(*args, **kwargs)
        if isinstance(response, werkzeug.Response):
            return response
        unpacked = unpack(response)
        status_code = unpacked[1] or http.OK
        schema = __schemas__.get(status_code, __schemas__.get('default'))
        if schema and __schemas__.get('_apply', True):
            schema = resolve_instance(schema['schema'])
            output = schema.dump(unpacked[0]).data
        else:
            output = unpacked[0]
        return format_output((format_response(output), ) + unpacked[1:])

    wrapped.__meta__['wrapped'] = True
    return wrapped

def format_output(values):
    while values[-1] is None:
        values = values[:-1]
    return values if len(values) > 1 else values[0]

def use_kwargs(args, default_in='query', inherit=True, apply=True):
    def wrapper(func):
        func.__dict__.setdefault('__args__', []).insert(0, {
            'args': args,
            'default_in': default_in,
            '_inherit': inherit,
            '_apply': apply,
        })
        return activate(func)
    return wrapper

def marshal_with(schema, code='default', description='', inherit=True, apply=True):
    def wrapper(func):
        func.__dict__.setdefault('__schemas__', []).insert(0, {
            code: {
                'schema': schema or {},
                'description': description,
            },
            '_inherit': inherit,
            '_apply': apply,
        })
        return activate(func)
    return wrapper

def doc(**kwargs):
    def wrapper(func):
        func.__apidoc__ = copy.deepcopy(getattr(func, '__apidoc__', {}))
        func.__apidoc__.update(kwargs)
        return func
    return wrapper

def resolve_parent(mro, key):
    for each in mro[1:]:
        try:
            return getattr(each, key)
        except AttributeError:
            pass
    return None

def merge_attrs(value, parent):
    merge_key(value, parent, '__args__')
    merge_key(value, parent, '__schemas__')
    return activate(value)

def merge_key(child, parent, attr):
    parent_value = copy.copy(getattr(parent, attr, []))
    child.__dict__.setdefault(attr, []).extend(parent_value)

class ResourceMeta(type):

    def __new__(mcs, name, bases, attrs):
        klass = super(ResourceMeta, mcs).__new__(mcs, name, bases, attrs)
        mro = klass.mro()
        for key, value in six.iteritems(attrs):
            if isinstance(value, types.FunctionType):
                parent = resolve_parent(mro, key)
                if parent is not None:
                    setattr(klass, key, merge_attrs(value, parent))
                if not isinstance(value, staticmethod):
                    value.__dict__.setdefault('__meta__', {})
                    value.__meta__['ismethod'] = True
        return klass
