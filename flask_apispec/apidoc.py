import copy
import functools

import apispec
from apispec.core import VALID_METHODS
from apispec.ext.marshmallow import MarshmallowPlugin

from marshmallow import Schema
from marshmallow.utils import is_instance_or_subclass

from flask_apispec.paths import rule_to_path, rule_to_params
from flask_apispec.utils import resolve_resource, resolve_annotations, merge_recursive

APISPEC_VERSION_INFO = tuple(
    [int(part) for part in apispec.__version__.split('.') if part.isdigit()]
)

class Converter:
    def __init__(self, app, spec, document_options=True):
        self.app = app
        self.spec = spec
        self.document_options = document_options
        try:
            self.marshmallow_plugin = next(
                plugin for plugin in self.spec.plugins
                if isinstance(plugin, MarshmallowPlugin)
            )
        except StopIteration:
            raise RuntimeError(
                "Must have a MarshmallowPlugin instance in the spec's list "
                'of plugins.'
            )

    def convert(self, target, endpoint=None, blueprint=None, **kwargs):
        endpoint = endpoint or target.__name__.lower()
        if blueprint:
            endpoint = '{}.{}'.format(blueprint, endpoint)
        rules = self.app.url_map._rules_by_endpoint[endpoint]
        return [self.get_path(rule, target, **kwargs) for rule in rules]

    def get_path(self, rule, target, **kwargs):
        operations = self.get_operations(rule, target)
        parent = self.get_parent(target, **kwargs)
        valid_methods = VALID_METHODS[self.spec.openapi_version.major]
        excluded_methods = {'head'}
        if not self.document_options:
            excluded_methods.add('options')
        return {
            'view': target,
            'path': rule_to_path(rule),
            'operations': {
                method.lower(): self.get_operation(rule, view, parent=parent)
                for method, view in operations.items()
                if method.lower() in (set(valid_methods) - excluded_methods)
            },
        }

    def get_operations(self, rule, target):
        return {}

    def get_operation(self, rule, view, parent=None):
        annotation = resolve_annotations(view, 'docs', parent)
        docs = merge_recursive(annotation.options)
        operation = {
            'responses': self.get_responses(view, parent),
            'parameters': self.get_parameters(rule, view, docs, parent),
        }
        docs.pop('params', None)
        return merge_recursive([operation, docs])

    def get_parent(self, view):
        return None

    def get_parameters(self, rule, view, docs, parent=None):
        openapi = self.marshmallow_plugin.converter
        annotation = resolve_annotations(view, 'args', parent)
        extra_params = []
        for args in annotation.options:
            schema = args.get('args', {})
            openapi_converter = openapi.schema2parameters
            if not is_instance_or_subclass(schema, Schema):
                if callable(schema):
                    schema = schema(request=None)
                else:
                    schema = Schema.from_dict(schema)
                    openapi_converter = functools.partial(
                        self._convert_dict_schema, openapi_converter)

            options = copy.copy(args.get('kwargs', {}))
            if not options.get('location'):
                options['location'] = 'body'
            extra_params += openapi_converter(schema, **options) if args else []

        rule_params = rule_to_params(rule, docs.get('params')) or []

        return extra_params + rule_params

    def get_responses(self, view, parent=None):
        annotation = resolve_annotations(view, 'schemas', parent)
        return merge_recursive(annotation.options)

    def _convert_dict_schema(self, openapi_converter, schema, location, **options):
        """When location is 'body' and OpenApi is 2, return one param for body fields.

        Otherwise return fields exactly as converted by apispec."""
        if self.spec.openapi_version.major < 3 and location == 'body':
            params = openapi_converter(schema, location=None, **options)
            body_parameter = {
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object",
                    "properties": {},
                },
            }
            for param in params:
                name = param["name"]
                body_parameter["schema"]["properties"].update({name: param})
                if param.get("required", False):
                    body_parameter["schema"].setdefault("required", []).append(name)
                del param["name"]
                del param["in"]
                del param["required"]
            return [body_parameter]

        return openapi_converter(schema, location=location, **options)

class ViewConverter(Converter):

    def get_operations(self, rule, view):
        return {method: view for method in rule.methods}

class ResourceConverter(Converter):

    def get_operations(self, rule, resource):
        return {
            method: getattr(resource, method.lower())
            for method in rule.methods
            if hasattr(resource, method.lower())
        }

    def get_parent(self, resource, **kwargs):
        return resolve_resource(resource, **kwargs)
