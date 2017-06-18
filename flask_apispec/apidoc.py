# -*- coding: utf-8 -*-

import copy

import six
from pkg_resources import parse_version

import apispec
from apispec.core import VALID_METHODS
from apispec.ext.marshmallow import swagger

from marshmallow import Schema
from marshmallow.utils import is_instance_or_subclass

from flask_apispec.paths import rule_to_path, rule_to_params
from flask_apispec.utils import resolve_instance, resolve_annotations, merge_recursive

class Converter(object):

    def __init__(self, app):
        self.app = app

    def convert(self, target, endpoint=None, blueprint=None, **kwargs):
        endpoint = endpoint or target.__name__.lower()
        if blueprint:
            endpoint = '{}.{}'.format(blueprint, endpoint)
        rules = self.app.url_map._rules_by_endpoint[endpoint]
        return [self.get_path(rule, target, **kwargs) for rule in rules]

    def get_path(self, rule, target, **kwargs):
        operations = self.get_operations(rule, target)
        parent = self.get_parent(target, **kwargs)
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
        converter = (
            swagger.schema2parameters
            if is_instance_or_subclass(args.get('args', {}), Schema)
            else swagger.fields2parameters
        )
        options = copy.copy(args.get('kwargs', {}))
        locations = options.pop('locations', None)
        if locations:
            options['default_in'] = locations[0]
        if parse_version(apispec.__version__) < parse_version('0.20.0'):
            options['dump'] = False

        rule_params = rule_to_params(rule, docs.get('params')) or []
        extra_params = converter(
            args.get('args', {}),
            **options
        ) if args else []

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
        return resolve_instance(resource, **kwargs)
