# -*- coding: utf-8 -*-

import re
import types

import six
from smore import swagger
from smore.apispec.core import VALID_METHODS

from flask_smore import ResourceMeta
from flask_smore.utils import resolve_refs, merge_recursive

class Documentation(object):

    def __init__(self, app, spec):
        self.app = app
        self.spec = spec
        self.view_converter = ViewConverter(app, spec)
        self.resource_converter = ResourceConverter(app, spec)

    def register(self, target, endpoint=None):
        if isinstance(target, types.FunctionType):
            self.view_converter.convert(target, endpoint)
        elif isinstance(target, ResourceMeta):
            self.resource_converter.convert(target, endpoint)
        else:
            raise TypeError

class Converter(object):

    def __init__(self, app, spec):
        self.app = app
        self.spec = spec

    def convert(self, target, endpoint=None):
        endpoint = endpoint or target.__name__
        rules = self.app.url_map._rules_by_endpoint[endpoint]
        for rule in rules:
            self.spec.add_path(**self.get_path(rule, target))

    def get_path(self, rule, target):
        operations = self.get_operations(rule, target)
        parent = self.get_parent(target)
        return {
            'view': target,
            'path': extract_path(rule.rule),
            'operations': {
                method.lower(): self.get_operation(view, parent=parent)
                for method, view in six.iteritems(operations)
                if method.lower() in (set(VALID_METHODS) - {'head'})
            },
        }

    def get_operation(self, view, parent=None):
        return {
            'responses': resolve_refs(parent, getattr(view, '__schemas__', {})),
            'parameters': self.get_parameters(view, parent),
        }

    def get_parent(self, view):
        return None

    def get_parameters(self, view, parent=None):
        __args__ = resolve_refs(parent, getattr(view, '__args__', {}))
        __apidoc__ = merge_recursive(
            getattr(view, '__apidoc__', {}),
            getattr(parent, '__apidoc__', {}),
        )
        return swagger.args2parameters(
            __args__.get('args', {}),
            default_in=__args__.get('default_in'),
        ) + __apidoc__.get('parameters', [])

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
        return resource

RE_URL = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')
def extract_path(path):
    return RE_URL.sub(r'{\1}', path)
