===========
flask-smore
===========

.. image:: https://img.shields.io/travis/jmcarp/flask-smore/master.svg
    :target: https://travis-ci.org/jmcarp/flask-smore
    :alt: Travis-CI

.. image:: https://img.shields.io/codecov/c/github/jmcarp/flask-smore/master.svg
    :target: https://codecov.io/github/jmcarp/flask-smore
    :alt: Code coverage

**flask-smore** is a lightweight tool for building REST APIs in Flask. **flask-smore** uses webargs_ for request parsing, marshmallow_ for response formatting, and smore_ to automatically generate Swagger markup. You can use **flask-smore** with vanilla Flask or a fuller-featured framework like Flask-RESTful_.

Install
-------

.. code-block::

    pip install flask-smore 

Quickstart
----------

.. code-block:: python

    from flask import Flask
    from flask_smore import use_kwargs, marshal_with

    from webargs import Arg
    from marshmallow import Schema

    from .models import Pet

    app = Flask(__name__)

    class PetSchema(Schema):
        class Meta:
            fields = ('name', 'category', 'size')

    @app.route('/pets')
    @use_kwargs({'category': Arg(str), 'size': Arg(int)})
    @marshal_with(PetSchema(many=True))
    def get_pets(**kwargs):
        return Pet.query.filter_by(**kwargs)

**flask-smore** works with function- and class-based views:

.. code-block:: python

    from flask import make_response
    from flask_smore.views import MethodResource

    class PetResource(MethodResource):

        @marshal_with(PetSchema)
        def get(self, pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

        @use_kwargs({'name': Arg(str), 'category': Arg(str)}, default_in='body')
        @marshal_with(PetSchema, code=201)
        def post(self, **kwargs):
            return Pet(**kwargs)

        @use_kwargs({'name': Arg(str), 'category': Arg(str)}, default_in='body')
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

**flask-smore** generates Swagger markup for your view functions and classes. By default, Swagger JSON is served at `/swagger/`, and Swagger-UI at `/swagger-ui/`.

.. code-block:: python

    from smore.apispec import APISpec
    from flask_smore.extension import FlaskSmore

    spec = APISpec(
        title='pets',
        version='v1',
        plugins=['smore.ext.marshmallow'],
    )
    docs = FlaskSmore(app, spec)

    docs.register(get_pets)
    docs.register(PetResource)

Notes
-----

**flask-smore** isn't stable yet, and the interface and internals may change. Bug reports and pull requests are much appreciated.

**flask-smore** is strongly inspired by Flask-RESTful_ and Flask-RESTplus_, but attempts to provide similar functionality with greater flexibility and less code.

.. _webargs: https://webargs.readthedocs.org/
.. _marshmallow: https://marshmallow.readthedocs.org/
.. _smore: https://smore.readthedocs.org/
.. _Flask-RESTful: https://flask-restful.readthedocs.org/
.. _Flask-RESTplus: https://flask-restplus.readthedocs.org/
