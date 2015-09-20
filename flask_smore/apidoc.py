# -*- coding: utf-8 -*-

import six
from smore import swagger
from smore.apispec.core import VALID_METHODS

from flask_smore.paths import rule_to_path, rule_to_params
from flask_smore.utils import resolve_instance, resolve_annotations, merge_recursive

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
        docs = resolve_annotations(view, 'docs', parent)
        operation = {
            'responses': self.get_responses(view, parent),
            'parameters': self.get_parameters(rule, view, docs, parent),
        }
        docs.options.pop('params', None)
        return merge_recursive(operation, docs.options)

    def get_parent(self, view):
        return None

    def get_parameters(self, rule, view, docs, parent=None):
        __args__ = resolve_annotations(view, 'args', parent)
        return swagger.args2parameters(
            __args__.options.get('args', {}),
            default_in=__args__.options.get('default_in'),
        ) + rule_to_params(rule, docs.options.get('params'))

    def get_responses(self, view, parent=None):
        return resolve_annotations(view, 'schemas', parent).options

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
