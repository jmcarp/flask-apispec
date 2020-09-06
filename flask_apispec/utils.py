import functools

import marshmallow as ma


def resolve_resource(resource, **kwargs):
    resource_class_args = kwargs.get('resource_class_args') or ()
    resource_class_kwargs = kwargs.get('resource_class_kwargs') or {}
    if isinstance(resource, type):
        return resource(*resource_class_args, **resource_class_kwargs)
    return resource


def resolve_schema(schema, request=None):
    if isinstance(schema, type) and issubclass(schema, ma.Schema):
        schema = schema()
    elif callable(schema):
        schema = schema(request)
    return schema

class Ref:

    def __init__(self, key):
        self.key = key

    def resolve(self, obj):
        return getattr(obj, self.key, None)


def resolve_refs(obj, attr):
    if isinstance(attr, dict):
        return {
            key: resolve_refs(obj, value)
            for key, value in attr.items()
        }
    if isinstance(attr, list):
        return [resolve_refs(obj, value) for value in attr]
    if isinstance(attr, Ref):
        return attr.resolve(obj)
    return attr

class Annotation:

    def __init__(self, options=None, inherit=None, apply=None):
        self.options = options or []
        self.inherit = inherit
        self.apply = apply

    def __eq__(self, other):
        if isinstance(other, Annotation):
            return (
                self.options == other.options and
                self.inherit == other.inherit and
                self.apply == other.apply
            )
        return NotImplemented

    def __ne__(self, other):
        ret = self.__eq__(other)
        return ret if ret is NotImplemented else not ret

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
            self.options + other.options,
            inherit=other.inherit,
            apply=self.apply if self.apply is not None else other.apply,
        )

def resolve_annotations(func, key, parent=None):
    annotations = (
        getattr(func, '__apispec__', {}).get(key, []) +
        getattr(parent, '__apispec__', {}).get(key, [])
    )
    return functools.reduce(
        lambda first, second: first.merge(second),
        [annotation.resolve(parent) for annotation in annotations],
        Annotation(),
    )

def merge_recursive(values):
    return functools.reduce(_merge_recursive, values, {})

def _merge_recursive(child, parent):
    if isinstance(child, dict) or isinstance(parent, dict):
        child = child or {}
        parent = parent or {}
        keys = set(child.keys()).union(parent.keys())
        return {
            key: _merge_recursive(child.get(key), parent.get(key))
            for key in keys
        }
    return child if child is not None else parent
