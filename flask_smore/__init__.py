# -*- coding: utf-8 -*-

__version__ = '0.1.0'

import copy
import types
import functools

import six
from six.moves import http_client as http

import flask
from webargs.flaskparser import parser

from flask_smore.utils import resolve_refs, merge_recursive

def unpack(resp):
    resp = resp if isinstance(resp, tuple) else (resp, )
    return resp + (None, ) * (3 - len(resp))

def resolve_instance(schema):
    if isinstance(schema, type):
        return schema()
    return schema

def activate(func):
    if getattr(func, '__wrapped__', False):
        return func

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        obj = args[0] if getattr(func, '__ismethod__', False) else None
        __args__ = resolve_refs(obj, getattr(func, '__args__', {}))
        __schemas__ = resolve_refs(obj, getattr(func, '__schemas__', {}))
        kwargs.update(parser.parse(__args__.get('args', {})))
        response = func(*args, **kwargs)
        unpacked = unpack(response)
        status_code = unpacked[1] or http.OK
        schema = __schemas__.get(status_code, __schemas__.get('default'))
        if schema:
            schema = resolve_instance(schema['schema'])
            return (flask.jsonify(schema.dump(unpacked[0]).data), ) + unpacked[1:]
        return (flask.jsonify(unpacked[0]), ) + unpacked[1:]

    wrapped.__wrapped__ = True
    return wrapped

def use_kwargs(args, default_in='query', inherit=True):
    def wrapper(func):
        func.__dict__.setdefault('__args__', {}).update({
            'args': args,
            'default_in': default_in,
            'inherit': inherit,
        })
        return activate(func)
    return wrapper

def marshal_with(schema, code='default', description='', inherit=True):
    def wrapper(func):
        func.__dict__.setdefault('__schemas__', {}).update({
            code: {
                'schema': schema,
                'description': description,
            },
            'inherit': inherit,
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
    child_value = getattr(child, attr, {})
    if child_value.get('inherit', True):
        parent_value = getattr(parent, attr, {})
        value = merge_recursive(child_value, parent_value)
        child.__dict__.setdefault(attr, {}).update(value)

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
                    value.__ismethod__ = True
        return klass
