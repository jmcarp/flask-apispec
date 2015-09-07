# -*- coding: utf-8 -*-

import flask
import pytest
import webtest

from webargs import Arg
import marshmallow as ma

from flask_smore import use_kwargs, marshal_with

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
