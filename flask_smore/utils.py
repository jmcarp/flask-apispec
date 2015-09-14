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

def resolve_annotations(obj, annotations):
    annotations = annotations or []
    return merge_recursive(*[resolve_refs(obj, each) for each in annotations])

def merge_recursive(*values):
    return functools.reduce(merge_recursive_pair, while_inherit(values), {})

def while_inherit(values):
    for value in values:
        yield value
        if not value.get('_inherit', True):
            break

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

def filter_recursive(data, predicate):
    if isinstance(data, dict):
        return {
            key: filter_recursive(value, predicate) for key, value in six.iteritems(data)
            if predicate(key, value)
        }
    return data
