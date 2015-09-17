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

from flask_smore.utils import resolve_instance, resolve_annotations, Annotation

def identity(value):
    return value

def unpack(resp):
    resp = resp if isinstance(resp, tuple) else (resp, )
    return resp + (None, ) * (3 - len(resp))

def activate(func):
    if getattr(func, '__smore__', {}).get('wrapped'):
        return func

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        config = flask.current_app.config
        parser = config.get('SMORE_WEBARGS_PARSER', flaskparser.parser)
        format_response = config.get('SMORE_FORMAT_RESPONSE', flask.jsonify) or identity

        obj = args[0] if func.__smore__.get('ismethod') else None
        __args__ = resolve_annotations(func, 'args', obj)
        __schemas__ = resolve_annotations(func, 'schemas', obj)
        if __args__.apply is not False:
            kwargs.update(parser.parse(__args__.options.get('args', {})))
        response = func(*args, **kwargs)
        if isinstance(response, werkzeug.Response):
            return response
        unpacked = unpack(response)
        status_code = unpacked[1] or http.OK
        schema = __schemas__.options.get(status_code, __schemas__.options.get('default'))
        if schema and __schemas__.apply is not False:
            schema = resolve_instance(schema['schema'])
            output = schema.dump(unpacked[0]).data
        else:
            output = unpacked[0]
        return format_output((format_response(output), ) + unpacked[1:])

    wrapped.__smore__['wrapped'] = True
    return wrapped

def format_output(values):
    while values[-1] is None:
        values = values[:-1]
    return values if len(values) > 1 else values[0]

def use_kwargs(args, default_in='query', inherit=True, apply=True):
    """Inject keyword arguments from the specified webargs arguments into the
    decorated view function.

    Usage:

    .. code-block:: python

        from webargs import Arg

        @use_kwargs({'name': Arg(str), 'category': Arg(str)})
        def get_pets(**kwargs):
            return Pet.query.filter_by(**kwargs).all()

    :param args: Mapping of argument names to `Arg` objects
    :param default_in: Optional default parameter location
    :param inherit: Inherit args from parent classes
    :param apply: Parse request with specified args
    """
    def wrapper(func):
        options = {
            'args': args,
            'default_in': default_in,
        }
        annotate(func, 'args', options, inherit=inherit, apply=apply)
        return activate(func)
    return wrapper

def marshal_with(schema, code='default', description='', inherit=True, apply=True):
    """Marshal the return value of the decorated view function using the
    specified schema.

    Usage:

    .. code-block:: python

        class PetSchema(Schema):
            class Meta:
                fields = ('name', 'category')

        @marshal_with(PetSchema)
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

    :param schema: Marshmallow schema class or instance, or `None`
    :param code: Optional HTTP response code
    :param description: Optional response description
    :param inherit: Inherit schemas from parent classes
    :param apply: Marshal response with specified schema
    """
    def wrapper(func):
        options = {
            code: {
                'schema': schema or {},
                'description': description,
            },
        }
        annotate(func, 'schemas', options, inherit=inherit, apply=apply)
        return activate(func)
    return wrapper

def annotate(func, key, options, **kwargs):
    annotation = Annotation(options, **kwargs)
    func.__dict__.setdefault('__smore__', {}).setdefault(key, []).insert(0, annotation)

def doc(**kwargs):
    """Annotate the decorated view function or class with the specified Swagger
    attributes.

    Usage:

    .. code-block:: python

        @doc(tags=['pet'], description='a pet store')
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()
    """
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
    merge_key(value, parent, 'args')
    merge_key(value, parent, 'schemas')
    return activate(value)

def merge_key(child, parent, attr):
    parent_value = getattr(parent, '__smore__', {}).get(attr, [])
    child.__dict__.setdefault('__smore__', {}).setdefault(attr, []).extend(parent_value)

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
                    value.__dict__.setdefault('__smore__', {})
                    value.__smore__['ismethod'] = True
        return klass
