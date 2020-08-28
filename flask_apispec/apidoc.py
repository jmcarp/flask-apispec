import copy

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
        if APISPEC_VERSION_INFO[0] < 3:
            openapi = self.marshmallow_plugin.openapi
        else:
            openapi = self.marshmallow_plugin.converter
        annotation = resolve_annotations(view, 'args', parent)
        extra_params = []
        for args in annotation.options:
            schema = args.get('args', {})
            if is_instance_or_subclass(schema, Schema):
                converter = openapi.schema2parameters
            elif callable(schema):
                schema = schema(request=None)
                if is_instance_or_subclass(schema, Schema):
                    converter = openapi.schema2parameters
                else:
                    converter = openapi.fields2parameters
            else:
                converter = openapi.fields2parameters
            options = copy.copy(args.get('kwargs', {}))
            location = options.pop('location', None)
            if location:
                options['default_in'] = location
            elif 'default_in' not in options:
                options['default_in'] = 'body'
            extra_params += converter(schema, **options) if args else []

        rule_params = rule_to_params(rule, docs.get('params')) or []

        return extra_params + rule_params

    def get_responses(self, view, parent=None):
        annotation = resolve_annotations(view, 'schemas', parent)
        return merge_recursive(annotation.options)

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
