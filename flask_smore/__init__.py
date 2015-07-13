# -*- coding: utf-8 -*-

import copy
import http
import types
import functools

import six
from webargs import flaskparser

def unpack(resp):
    resp = resp if isinstance(resp, tuple) else (resp, )
    return resp + (None, ) * (3 - len(resp))

def activate(func):
    if getattr(func, '__wrapped__', False):
        return func

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if getattr(func, '__args__', None):
            kwargs.update(flaskparser.parse(func.__args__))
        response = func(*args, **kwargs)
        unpacked = unpack(response)
        status_code = unpacked[1] or http.client.OK
        schema = getattr(func, '__schemas__', {}).get(status_code)
        if schema:
            return (schema['schema'].dump(unpacked[0]).data, ) + unpacked[1:]
        return unpacked
    return wrapped

def use_kwargs(args, default_in='query'):
    def wrapper(func):
        func.__dict__.setdefault('__args__', {}).update({
            'args': args,
            'default_in': default_in,
        })
        return activate(func)
    return wrapper

def marshal_with(schema, code=http.client.OK, description=None):
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
    value.__schemas__ = getattr(value, '__schemas__', {})
    value.__schemas__.update({
        key: val for key, val in six.iteritems(getattr(parent, '__schemas__', {}))
        if key not in value.__schemas__
    })
    return activate(value)

class ResourceMeta(type):

    def __new__(mcs, name, bases, attrs):
        klass = super(ResourceMeta, mcs).__new__(mcs, name, bases, attrs)
        mro = klass.mro()
        for key, value in six.iteritems(attrs):
            if isinstance(value, types.FunctionType):
                parent = resolve_parent(mro, key)
                if parent is not None:
                    setattr(klass, key, merge_attrs(value, parent))
        return klass
