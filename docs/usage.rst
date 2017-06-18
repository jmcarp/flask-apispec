.. _quickstart:

Usage
=====

Decorators
----------

Use the :func:`use_kwargs <flask_apispec.annotations.use_kwargs>` and :func:`marshal_with <flask_apispec.annotations.marshal_with>` decorators on functions, methods, or classes to declare request parsing and response marshalling behavior, respectively.

.. code-block:: python

    import flask
    from webargs import fields
    from flask_apispec import use_kwargs, marshal_with

    from .models import Pet
    from .schemas import PetSchema

    app = flask.Flask(__name__)

    @app.route('/pets')
    @use_kwargs({'species': fields.Str()})
    @marshal_with(PetSchema(many=True))
    def list_pets(**kwargs):
        return Pet.query.filter_by(**kwargs).all()

Decorators can also be applied to view classes, e.g. Flask's :class:`MethodView <flask.views.MethodView>` or flask-restful's :class:`Resource <flask_restful.Resource>`. For correct inheritance behavior, view classes should use the `ResourceMeta` meta-class; for convenience, **flask-apispec** provides `MethodResource`, which inherits from `MethodView` and uses the `ResourceMeta` and `MethodViewType` meta-classes.

.. code-block:: python

    from flask_apispec import MethodResource

    @marshal_with(PetSchema)
    class StoreResource(MethodResource):

        def get(self, pet_id):
            return Pet.query.filter_by(id=pet_id).one()

        @use_kwargs(PetSchema)
        def put(self, pet_id, **kwargs):
            pet = Pet.query.filter_by(id=pet_id).one()
            for key, value in kwargs.items():
                setattr(pet, key, value)
            session.add(pet)
            session.commit()
            return pet

        @marshal_with(None, code=204)
        def delete(self, pet_id):
            pet = Pet.query.filter_by(id=pet_id).one()
            session.delete(pet)
            session.commit()
            return None

Inheritance
-----------

Subclasses of view classes inherit both class and method decorators. Method decorators are inherited by method name. This makes it possible to add a new decorator in a subclass without repeating all existing decorators.

.. code-block:: python

    class PetResource(MethodResource):

        @use_kwargs({'species': fields.Str()})
        @marshal_with(PetSchema)
        def get(self, **kwargs):
            return Pet.query.filter_by(**kwargs).all()

    class PetResourceExtended(PetResource):

        @use_kwargs({'indoor': fields.Bool()})
        def get(self, **kwargs):
            return super(PetResourceExtended, self)(**kwargs)

To allow subclasses to flexibly override parent settings, **flask-apispec** also provides the `Ref` helper. Using `Ref` looks up variables by name on the associated class at runtime. In this example, all methods in the `PetResource` view class serialize their outputs with `PetSchema`.

.. code-block:: python

    from flask_apispec import Ref

    @marshal_with(Ref('schema'))
    class BaseResource(MethodResource):

        schema = None

    class PetResource(BaseResource):

        schema = PetSchema

        def get(self, pet_id):
            return Pet.query.filter_by(id=pet_id).one()

Swagger documentation
---------------------

**flask-apispec** automatically generates Swagger 2.0 documentation for view functions and classes using apispec_.

.. code-block:: python

    from flask_apispec import FlaskApiSpec

    docs = FlaskApiSpec(app)

    docs.register(list_pets)

    app.add_url_rule('/stores', view_func=StoreResource.as_view('Store'))
    docs.register(StoreResource)

By default, **flask-apispec** serves Swagger JSON at /swagger and Swagger UI at /swagger-ui. To override either URL, set the `APISPEC_SWAGGER_URL` and `APISPEC_SWAGGER_UI_URL` variables on the Flask application config, respectively. To disable serving either resource, set the corresponding configuration variable to `None`.

To add Swagger markup that is not currently supported by apispec_, use the :func:`doc <flask_apispec.annotations.doc>` decorator:

.. code-block:: python

    @doc(description='a pet store', tags=['pets'])
    class PetResource(MethodResource):
        pass

.. _webargs: https://webargs.readthedocs.io/
.. _marshmallow: https://marshmallow.readthedocs.io/
.. _apispec: https://apispec.readthedocs.io/
