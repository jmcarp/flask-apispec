# -*- coding: utf-8 -*-

import six
import pytest
import webtest

import flask
import flask.views

from webargs import Arg
import marshmallow as ma

from flask_smore.utils import Ref
from flask_smore import ResourceMeta, use_kwargs, marshal_with

class Bunch(object):

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    def items(self):
        return self.__dict__.items()

@pytest.fixture
def app():
    return flask.Flask(__name__)

@pytest.fixture
def client(app):
    return webtest.TestApp(app)

@pytest.fixture
def models():
    class Band(object):
        def __init__(self, name, genre):
            self.name = name
            self.genre = genre

    return Bunch(Band=Band)

@pytest.fixture
def schemas(models):
    class BandSchema(ma.Schema):
        class Meta:
            fields = ('name', 'genre')

    return Bunch(BandSchema=BandSchema)

class MethodResourceMeta(ResourceMeta, flask.views.MethodViewType):
    pass

class MethodResource(six.with_metaclass(MethodResourceMeta, flask.views.MethodView)):
    methods = None

class TestFunctionViews:

    def test_use_kwargs(self, app, client):
        @app.route('/')
        @use_kwargs({'name': Arg(str)})
        def view(**kwargs):
            return {'name': kwargs['name']}
        res = client.get('/', {'name': 'freddie'})
        assert res.json == {'name': 'freddie'}

    def test_marshal_with_default(self, app, client, models, schemas):
        @app.route('/')
        @marshal_with(schemas.BandSchema)
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_marshal_with_codes(self, app, client, models, schemas):
        @app.route('/')
        @marshal_with(schemas.BandSchema)
        @marshal_with(schemas.BandSchema(only=('name', )), code=201)
        def view():
            return models.Band('queen', 'rock'), 201
        res = client.get('/')
        assert res.json == {'name': 'queen'}

class TestClassViews:

    def test_kwargs_inheritance(self, app, client):
        class BaseResource(MethodResource):
            @use_kwargs({'name': Arg(str)})
            def get(self, **kwargs):
                pass

        class ConcreteResource(BaseResource):
            @use_kwargs({'genre': Arg(str)})
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_schemas_inheritance(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            @marshal_with(schemas.BandSchema)
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            @marshal_with(schemas.BandSchema(only=('genre', )), code=201)
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

    def test_schemas_inheritance_refs(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            schema = None

            @marshal_with(Ref('schema'))
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            schema = schemas.BandSchema

            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze')

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'name': 'slowdive', 'genre': 'shoegaze'}
