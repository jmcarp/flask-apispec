# -*- coding: utf-8 -*-

__version__ = '0.1.1'

import functools

import six
from six.moves import http_client as http

import flask
from flask.views import http_method_funcs

import werkzeug
from webargs import flaskparser

from flask_smore.utils import resolve_instance, resolve_annotations, Annotation

def identity(value):
    return value

def unpack(resp):
    resp = resp if isinstance(resp, tuple) else (resp, )
    return resp + (None, ) * (3 - len(resp))

class Wrapper(object):
    """Apply annotations to a view function.

    :param func: View function to wrap
    :param instance: Optional instance or parent
    """
    def __init__(self, func, instance=None):
        self.func = func
        self.instance = instance

    def __call__(self, *args, **kwargs):
        response = self.call_view(*args, **kwargs)
        if isinstance(response, werkzeug.Response):
            return response
        unpacked = unpack(response)
        status_code = unpacked[1] or http.OK
        return self.marshal_result(unpacked, status_code)

    def call_view(self, *args, **kwargs):
        config = flask.current_app.config
        parser = config.get('SMORE_WEBARGS_PARSER', flaskparser.parser)
        __args__ = resolve_annotations(self.func, 'args', self.instance)
        if __args__.apply is not False:
            kwargs.update(parser.parse(__args__.options.get('args', {})))
        return self.func(*args, **kwargs)

    def marshal_result(self, unpacked, status_code):
        config = flask.current_app.config
        format_response = config.get('SMORE_FORMAT_RESPONSE', flask.jsonify) or identity
        __schemas__ = resolve_annotations(self.func, 'schemas', self.instance)
        schema = __schemas__.options.get(status_code, __schemas__.options.get('default'))
        if schema and __schemas__.apply is not False:
            schema = resolve_instance(schema['schema'])
            output = schema.dump(unpacked[0]).data
        else:
            output = unpacked[0]
        return format_output((format_response(output), ) + unpacked[1:])

def activate(func):
    if isinstance(func, type) or getattr(func, '__smore__', {}).get('wrapped'):
        return func

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        instance = args[0] if func.__smore__.get('ismethod') else None
        wrapper_cls = resolve_annotations(func, 'wrapper', instance)
        wrapper = wrapper_cls.options.get('wrapper', Wrapper)(func, instance)
        return wrapper(*args, **kwargs)

    wrapped.__smore__['wrapped'] = True
    return wrapped

def format_output(values):
    while values[-1] is None:
        values = values[:-1]
    return values if len(values) > 1 else values[0]

def use_kwargs(args, default_in='query', inherit=None, apply=None):
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

def marshal_with(schema, code='default', description='', inherit=None, apply=None):
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

def doc(inherit=None, **kwargs):
    """Annotate the decorated view function or class with the specified Swagger
    attributes.

    Usage:

    .. code-block:: python

        @doc(tags=['pet'], description='a pet store')
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

    :param inherit: Inherit Swagger documentation from parent classes
    """
    def wrapper(func):
        annotate(func, 'docs', kwargs, inherit=inherit)
        return activate(func)
    return wrapper

def wrap_with(wrapper_cls):
    """Use a custom `Wrapper` to apply annotations to the decorated function.

    :param wrapper_cls: Custom `Wrapper` subclass
    """
    def wrapper(func):
        annotate(func, 'wrapper', {'wrapper': wrapper_cls})
        return activate(func)
    return wrapper

def annotate(func, key, options, **kwargs):
    annotation = Annotation(options, **kwargs)
    func.__smore__ = func.__dict__.get('__smore__', {})
    func.__smore__.setdefault(key, []).insert(0, annotation)

def inherit(child, parents):
    child.__smore__ = child.__dict__.get('__smore__', {})
    for key in ['args', 'schemas', 'docs']:
        child.__smore__.setdefault(key, []).extend(
            annotation
            for parent in parents
            for annotation in getattr(parent, '__smore__', {}).get(key, [])
            if annotation not in child.__smore__[key]
        )

class ResourceMeta(type):

    def __new__(mcs, name, bases, attrs):
        klass = super(ResourceMeta, mcs).__new__(mcs, name, bases, attrs)
        mro = klass.mro()
        inherit(klass, mro[1:])
        methods = [
            each.lower() for each in
            getattr(klass, 'methods', None) or http_method_funcs
        ]
        for key, value in six.iteritems(attrs):
            if key.lower() in methods:
                parents = [
                    getattr(parent, key) for parent in mro
                    if hasattr(parent, key)
                ]
                inherit(value, parents)
                setattr(klass, key, activate(value))
                if not isinstance(value, staticmethod):
                    value.__dict__.setdefault('__smore__', {})
                    value.__smore__['ismethod'] = True
        return klass
