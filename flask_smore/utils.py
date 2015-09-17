# -*- coding: utf-8 -*-

import functools

import six

class Ref(object):

    def __init__(self, key):
        self.key = key

    def resolve(self, obj):
        return getattr(obj, self.key, None)

def resolve_refs(obj, attr):
    if isinstance(attr, dict):
        return {
            key: resolve_refs(obj, value)
            for key, value in six.iteritems(attr)
        }
    if isinstance(attr, Ref):
        return attr.resolve(obj)
    return attr

def resolve_instance(schema):
    if isinstance(schema, type):
        return schema()
    return schema

class Annotation(object):

    def __init__(self, options=None, inherit=None, apply=None):
        self.options = options or {}
        self.inherit = inherit
        self.apply = apply

    def resolve(self, obj):
        return self.__class__(
            resolve_refs(obj, self.options),
            inherit=self.inherit,
            apply=self.apply,
        )

    def merge(self, other):
        if self.inherit is False:
            return self
        return self.__class__(
            merge_recursive_pair(self.options, other.options),
            inherit=other.inherit,
            apply=self.apply if self.apply is not None else other.apply,
        )

def resolve_annotations(obj, annotations):
    annotations = annotations or []
    return functools.reduce(
        lambda first, second: first.merge(second),
        [annotation.resolve(obj) for annotation in annotations],
        Annotation(),
    )

def merge_recursive_pair(child, parent):
    if isinstance(child, dict) or isinstance(parent, dict):
        child = child or {}
        parent = parent or {}
        keys = set(child.keys()).union(parent.keys())
        return {
            key: merge_recursive_pair(child.get(key), parent.get(key))
            for key in keys
        }
    return child if child is not None else parent
