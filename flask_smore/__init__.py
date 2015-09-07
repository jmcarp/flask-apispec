# -*- coding: utf-8 -*-

import copy
import http
import types
import functools

import six
import flask
from webargs.flaskparser import parser

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
        status_code = unpacked[1] or http.client.OK
        schema = __schemas__.get(status_code, __schemas__.get('default'))
        if schema:
            schema = resolve_instance(schema['schema'])
            return (flask.jsonify(schema.dump(unpacked[0]).data), ) + unpacked[1:]
        return (flask.jsonify(unpacked[0]), ) + unpacked[1:]

    wrapped.__wrapped__ = True
    return wrapped

def use_kwargs(args, default_in='query'):
    def wrapper(func):
        func.__dict__.setdefault('__args__', {}).update({
            'args': args,
            'default_in': default_in,
        })
        return activate(func)
    return wrapper

def marshal_with(schema, code='default', description=''):
    def wrapper(func):
        func.__dict__.setdefault('__schemas__', {}).update({
            code: {
                'schema': schema,
                'description': description,
            }
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
    value = merge_recursive(
        getattr(child, attr, {}),
        getattr(parent, attr, {}),
    )
    setattr(child, attr, value)

def merge_recursive(child, parent):
    if isinstance(child, dict) or isinstance(parent, dict):
        child = child or {}
        parent = parent or {}
        keys = set(child.keys()).union(parent.keys())
        return {
            key: merge_recursive(child.get(key), parent.get(key))
            for key in keys
        }
    return child or parent

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

class Ref(object):

    def __init__(self, key):
        self.key = key

    def resolve(self, obj):
        return getattr(obj, self.key, None)

def resolve_refs(obj, attr):
    if isinstance(attr, dict):
        return {
            key: resolve_refs(obj, value)
            for key, value in six.iteritems(attr)
        }
    if isinstance(attr, Ref):
        return attr.resolve(obj)
    return attr
