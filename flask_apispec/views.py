import flask.views

from flask_apispec.annotations import activate


def inherit(child, parents):
    child.__apispec__ = child.__dict__.get('__apispec__', {})
    for key in ['args', 'schemas', 'docs']:
        child.__apispec__.setdefault(key, []).extend(
            annotation
            for parent in parents
            for annotation in getattr(parent, '__apispec__', {}).get(key, [])
            if annotation not in child.__apispec__[key]
        )


class ResourceMeta(type):

    def __new__(mcs, name, bases, attrs):
        klass = super().__new__(mcs, name, bases, attrs)
        mro = klass.mro()
        inherit(klass, mro[1:])
        methods = [
            each.lower() for each in
            getattr(klass, 'methods', None) or flask.views.http_method_funcs
        ]
        for key, value in attrs.items():
            if key.lower() in methods:
                parents = [
                    getattr(parent, key) for parent in mro
                    if hasattr(parent, key)
                ]
                inherit(value, parents)
                setattr(klass, key, activate(value))
                if not isinstance(value, staticmethod):
                    value.__dict__.setdefault('__apispec__', {})
                    value.__apispec__['ismethod'] = True
        return klass


class MethodResourceMeta(ResourceMeta, type(flask.views.MethodView)):
    pass


class MethodResource(flask.views.MethodView, metaclass=MethodResourceMeta):
    """Subclass of `MethodView` that uses the `ResourceMeta` metaclass. Behaves
    exactly like `MethodView` but inherits **flask-apispec** annotations.
    """
    methods = None
