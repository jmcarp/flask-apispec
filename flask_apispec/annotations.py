import functools

from flask_apispec import utils
from flask_apispec.wrapper import Wrapper


def use_kwargs(args, location=None, inherit=None, apply=None, **kwargs):
    """Inject keyword arguments from the specified webargs arguments into the
    decorated view function.

    Usage:

    .. code-block:: python

        from marshmallow import fields

        @use_kwargs({'name': fields.Str(), 'category': fields.Str()})
        def get_pets(**kwargs):
            return Pet.query.filter_by(**kwargs).all()

    :param args: Mapping of argument names to :class:`Field <marshmallow.fields.Field>`
        objects, :class:`Schema <marshmallow.Schema>`, or a callable which accepts a
        request and returns a :class:`Schema <marshmallow.Schema>`
    :param location: Default request location to parse
    :param inherit: Inherit args from parent classes
    :param apply: Parse request with specified args
    """

    kwargs.update({'location': location})

    def wrapper(func):
        options = {
            'args': args,
            'kwargs': kwargs,
        }
        annotate(func, 'args', [options], inherit=inherit, apply=apply)
        return activate(func)
    return wrapper


def marshal_with(schema, code='default', description='', inherit=None, apply=None):
    """Marshal the return value of the decorated view function using the
    specified schema.

    Usage:

    .. code-block:: python

        class PetSchema(Schema):
            class Meta:
                fields = ('name', 'category')

        @marshal_with(PetSchema)
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

    :param schema: :class:`Schema <marshmallow.Schema>` class or instance, or `None`
    :param code: Optional HTTP response code
    :param description: Optional response description
    :param inherit: Inherit schemas from parent classes
    :param apply: Marshal response with specified schema
    """
    def wrapper(func):
        options = {
            code: {
                'schema': schema or {},
                'description': description,
            },
        }
        annotate(func, 'schemas', [options], inherit=inherit, apply=apply)
        return activate(func)
    return wrapper


def doc(inherit=None, **kwargs):
    """Annotate the decorated view function or class with the specified Swagger
    attributes.

    Usage:

    .. code-block:: python

        @doc(tags=['pet'], description='a pet store')
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

    :param inherit: Inherit Swagger documentation from parent classes
    """
    def wrapper(func):
        annotate(func, 'docs', [kwargs], inherit=inherit)
        return activate(func)
    return wrapper


def wrap_with(wrapper_cls):
    """Use a custom `Wrapper` to apply annotations to the decorated function.

    :param wrapper_cls: Custom `Wrapper` subclass
    """
    def wrapper(func):
        annotate(func, 'wrapper', [{'wrapper': wrapper_cls}])
        return activate(func)
    return wrapper


def annotate(func, key, options, **kwargs):
    annotation = utils.Annotation(options, **kwargs)
    func.__apispec__ = func.__dict__.get('__apispec__', {})
    func.__apispec__.setdefault(key, []).insert(0, annotation)


def activate(func):
    if isinstance(func, type) or getattr(func, '__apispec__', {}).get('wrapped'):
        return func

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        instance = args[0] if func.__apispec__.get('ismethod') else None
        annotation = utils.resolve_annotations(func, 'wrapper', instance)
        wrapper_cls = utils.merge_recursive(annotation.options).get('wrapper', Wrapper)
        wrapper = wrapper_cls(func, instance)
        return wrapper(*args, **kwargs)

    wrapped.__apispec__['wrapped'] = True
    return wrapped
