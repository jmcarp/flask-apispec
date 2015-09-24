# -*- coding: utf-8 -*-

import types

import six
from smore import swagger
from smore.apispec.core import VALID_METHODS

from flask_smore import ResourceMeta
from flask_smore.paths import rule_to_path, rule_to_params
from flask_smore.utils import resolve_instance, resolve_annotations, merge_recursive

class Documentation(object):
    """API documentation collector.

    Usage:

    .. code-block:: python

        app = Flask(__name__)
        spec = APISpec(title='pets', version='v1', plugins=['smore.ext.marshmallow'])
        docs = Documentation(app, spec)

        @app.route('/pet/<pet_id>')
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

        docs.register(get_pet)

    :param Flask app: App associated with API documentation
    :param APISpec spec: Smore specification associated with API documentation
    """
    def __init__(self, app, spec):
        self.app = app
        self.spec = spec
        self.view_converter = ViewConverter(app)
        self.resource_converter = ResourceConverter(app)

    def register(self, target, endpoint=None, blueprint=None):
        if isinstance(target, types.FunctionType):
            paths = self.view_converter.convert(target, endpoint, blueprint)
        elif isinstance(target, ResourceMeta):
            paths = self.resource_converter.convert(target, endpoint, blueprint)
        else:
            raise TypeError
        for path in paths:
            self.spec.add_path(**path)

class Converter(object):

    def __init__(self, app):
        self.app = app

    def convert(self, target, endpoint=None, blueprint=None):
        endpoint = endpoint or target.__name__.lower()
        if blueprint:
            endpoint = '{}.{}'.format(blueprint, endpoint)
        rules = self.app.url_map._rules_by_endpoint[endpoint]
        return [self.get_path(rule, target) for rule in rules]

    def get_path(self, rule, target):
        operations = self.get_operations(rule, target)
        parent = self.get_parent(target)
        return {
            'view': target,
            'path': rule_to_path(rule),
            'operations': {
                method.lower(): self.get_operation(rule, view, parent=parent)
                for method, view in six.iteritems(operations)
                if method.lower() in (set(VALID_METHODS) - {'head'})
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
        annotation = resolve_annotations(view, 'args', parent)
        args = merge_recursive(annotation.options)
        return swagger.fields2parameters(
            args.get('args', {}),
            **args.get('kwargs', {})
        ) + rule_to_params(rule, docs.get('params'))

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

    def get_parent(self, resource):
        return resolve_instance(resource)
