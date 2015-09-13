# -*- coding: utf-8 -*-

import flask

import pytest
import webtest

import marshmallow as ma

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
        name = ma.fields.Str()
        genre = ma.fields.Str()

    return Bunch(BandSchema=BandSchema)
