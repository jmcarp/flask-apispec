# -*- coding: utf-8 -*-
try:
    from collections.abc import Mapping
except ImportError:  # Python 2
    from collections import Mapping

from types import MethodType

import flask
import marshmallow as ma
import werkzeug
from six.moves import http_client as http
from webargs import flaskparser

from flask_apispec import utils


MARSHMALLOW_VERSION_INFO = tuple(
    [int(part) for part in ma.__version__.split('.') if part.isdigit()]
)

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
        view_fn = self.func
        config = flask.current_app.config
        parser = config.get('APISPEC_WEBARGS_PARSER', flaskparser.parser)
        # Delegate webargs.use_args annotations
        annotation = utils.resolve_annotations(self.func, 'args', self.instance)
        if annotation.apply is not False:
            for option in annotation.options:
                schema = utils.resolve_schema(option['argmap'], request=flask.request)
                view_fn = parser.use_args(schema, **option['kwargs'])(view_fn)
        # Delegate webargs.use_kwargs annotations
        annotation = utils.resolve_annotations(self.func, 'kwargs', self.instance)
        if annotation.apply is not False:
            for option in annotation.options:
                schema = utils.resolve_schema(option['argmap'], request=flask.request)
                if getattr(schema, 'many', False):
                    raise Exception("@use_kwargs cannot be used with a with a "
                                    "'many=True' schema, as it must deserialize "
                                    "to a dict")
                elif isinstance(schema, ma.Schema):
                    # Spy the post_load to provide a more informative error
                    # if it doesn't return a Mapping
                    post_load_fns = post_load_fn_names(schema)
                    for post_load_fn_name in post_load_fns:
                        spy_post_load(schema, post_load_fn_name)
                view_fn = parser.use_kwargs(schema, **option['kwargs'])(view_fn)
        return view_fn(*args, **kwargs)

    def marshal_result(self, unpacked, status_code):
        config = flask.current_app.config
        format_response = config.get('APISPEC_FORMAT_RESPONSE', flask.jsonify) or identity
        annotation = utils.resolve_annotations(self.func, 'schemas', self.instance)
        schemas = utils.merge_recursive(annotation.options)
        schema = schemas.get(status_code, schemas.get('default'))
        if schema and annotation.apply is not False:
            schema = utils.resolve_schema(schema['schema'], request=flask.request)
            dumped = schema.dump(unpacked[0])
            output = dumped.data if MARSHMALLOW_VERSION_INFO[0] < 3 else dumped
        else:
            output = unpacked[0]
        return format_output((format_response(output), ) + unpacked[1:])

def identity(value):
    return value

def unpack(resp):
    resp = resp if isinstance(resp, tuple) else (resp, )
    return resp + (None, ) * (3 - len(resp))

def format_output(values):
    while values[-1] is None:
        values = values[:-1]
    return values if len(values) > 1 else values[0]

def post_load_fn_names(schema):
    fn_names = []
    if hasattr(schema, '_hooks'):
        # Marshmallow >=3
        hooks = getattr(schema, '_hooks')
        for key in ((ma.decorators.POST_LOAD, True),
                    (ma.decorators.POST_LOAD, False)):
            if key in hooks:
                fn_names.append(*hooks[key])
    else:
        # Marshmallow <= 2
        processors = getattr(schema, '__processors__')
        for key in ((ma.decorators.POST_LOAD, True),
                    (ma.decorators.POST_LOAD, False)):
            if key in processors:
                fn_names.append(*processors[key])
    return fn_names

def spy_post_load(schema, post_load_fn_name):
    processor = getattr(schema, post_load_fn_name)

    def _spy_processor(_self, *args, **kwargs):
        rv = processor(*args, **kwargs)
        if not isinstance(rv, Mapping):
            raise Exception("The @use_kwargs decorator can only use Schemas that "
                            "return dicts, but the @post_load-annotated method "
                            "'{schema_type}.{post_load_fn_name}' returned: {rv}"
                            .format(schema_type=type(schema),
                                    post_load_fn_name=post_load_fn_name,
                                    rv=rv))
        return rv

    for attr in (
            # Marshmallow <= 2.x
            '__marshmallow_tags__',
            '__marshmallow_kwargs__',
            # Marshmallow >= 3.x
            '__marshmallow_hook__'
    ):
        if hasattr(processor, attr):
            setattr(_spy_processor, attr, getattr(processor, attr))
    setattr(schema, post_load_fn_name, MethodType(_spy_processor, schema))
