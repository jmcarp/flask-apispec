=============
flask-apispec
=============

.. image:: https://img.shields.io/pypi/v/flask-apispec.svg
    :target: http://badge.fury.io/py/flask-apispec
    :alt: Latest version

.. image:: https://readthedocs.org/projects/flask-apispec/badge/?version=latest
    :target: https://flask-apispec.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation status

.. image:: https://img.shields.io/travis/jmcarp/flask-apispec/master.svg
    :target: https://travis-ci.org/jmcarp/flask-apispec
    :alt: Travis-CI

.. image:: https://img.shields.io/codecov/c/github/jmcarp/flask-apispec/master.svg
    :target: https://codecov.io/github/jmcarp/flask-apispec
    :alt: Code coverage

**flask-apispec** is a lightweight tool for building REST APIs in Flask. **flask-apispec** uses webargs_ for request parsing, marshmallow_ for response formatting, and apispec_ to automatically generate Swagger markup. You can use **flask-apispec** with vanilla Flask or a fuller-featured framework like Flask-RESTful_.

Install
-------

::

    pip install flask-apispec

Quickstart
----------

.. code-block:: python

    from flask import Flask
    from flask_apispec import use_kwargs, marshal_with

    from marshmallow import fields, Schema

    from .models import Pet

    app = Flask(__name__)

    class PetSchema(Schema):
        class Meta:
            fields = ('name', 'category', 'size')

    @app.route('/pets')
    @use_kwargs({'category': fields.Str(), 'size': fields.Str()})
    @marshal_with(PetSchema(many=True))
    def get_pets(**kwargs):
        return Pet.query.filter_by(**kwargs)

**flask-apispec** works with function- and class-based views:

.. code-block:: python

    from flask import make_response
    from flask_apispec.views import MethodResource

    class PetResource(MethodResource):

        @marshal_with(PetSchema)
        def get(self, pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

        @use_kwargs(PetSchema)
        @marshal_with(PetSchema, code=201)
        def post(self, **kwargs):
            return Pet(**kwargs)

        @use_kwargs(PetSchema)
        @marshal_with(PetSchema)
        def put(self, pet_id, **kwargs):
            pet = Pet.query.filter(Pet.id == pet_id).one()
            pet.__dict__.update(**kwargs)
            return pet

        @marshal_with(None, code=204)
        def delete(self, pet_id):
            pet = Pet.query.filter(Pet.id == pet_id).one()
            pet.delete()
            return make_response('', 204)

**flask-apispec** generates Swagger markup for your view functions and classes. By default, Swagger JSON is served at `/swagger/`, and Swagger-UI at `/swagger-ui/`.

.. code-block:: python

    from apispec import APISpec
    from flask_apispec.extension import FlaskApiSpec

    app.config.update({
        'APISPEC_SPEC': APISpec(
            title='pets',
            version='v1',
            plugins=['apispec.ext.marshmallow'],
        ),
        'APISPEC_SWAGGER_URL': '/swagger/',
    })
    docs = FlaskApiSpec(app)

    docs.register(get_pets)
    docs.register(PetResource)

Documentation
-------------

https://flask-apispec.readthedocs.io/

Notes
-----

**flask-apispec** is strongly inspired by Flask-RESTful_ and Flask-RESTplus_, but attempts to provide similar functionality with greater flexibility and less code.

.. _webargs: https://webargs.readthedocs.io/
.. _marshmallow: https://marshmallow.readthedocs.io/
.. _apispec: https://apispec.readthedocs.io/
.. _Flask-RESTful: https://flask-restful.readthedocs.io/
.. _Flask-RESTplus: https://flask-restplus.readthedocs.io/
