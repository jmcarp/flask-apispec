# -*- coding: utf-8 -*-

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

def merge_recursive(child, parent):
    if isinstance(child, dict) or isinstance(parent, dict):
        child = child or {}
        parent = parent or {}
        keys = set(child.keys()).union(parent.keys())
        return {
            key: merge_recursive(child.get(key), parent.get(key))
            for key in keys
        }
    return child or parent

def filter_recursive(data, predicate):
    if isinstance(data, dict):
        return {
            key: filter_recursive(value, predicate) for key, value in six.iteritems(data)
            if predicate(key, value)
        }
    return data
