# -*- coding: utf-8 -*-

import six
from webargs import Arg
import marshmallow as ma

from flask_smore.utils import Ref
from flask_smore import ResourceMeta, doc, marshal_with, use_kwargs

class Pet:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class PetSchema(ma.Schema):
    name = ma.fields.Str()
    type = ma.fields.Str()

class PetResource(six.with_metaclass(ResourceMeta)):
    @use_kwargs({
        'category': Arg(str),
        'name': Arg(str),
    })
    @marshal_with(PetSchema(), code=200)
    def get(self):
        return Pet('calici', 'cat')

class CatResource(PetResource):
    @use_kwargs({'category': Arg(int)})
    @marshal_with(PetSchema(), code=201)
    def get(self):
        return Pet('calici', 'cat'), 200

###

class CrudResource(six.with_metaclass(ResourceMeta)):

    schema = None

    @marshal_with(Ref('schema'), code=200)
    def get(self, id):
        pass

    @marshal_with(Ref('schema'), code=200)
    @marshal_with(Ref('schema'), code=201)
    def post(self):
        pass

    @marshal_with(Ref('schema'), code=200)
    def put(self, id):
        pass

    @marshal_with(None, code=204)
    def delete(self, id):
        pass

class PetResource(CrudResource):
    schema = PetSchema

###

import flask
import flask.views
from smore.apispec import APISpec

from flask_smore.apidoc import Documentation

app = flask.Flask(__name__)
spec = APISpec(
    title='title',
    version='v1',
    plugins=['smore.ext.marshmallow'],
)
docs = Documentation(app, spec)

@app.route('/pets/<pet_id>')
@doc(parameters=[{'name': 'pet_id', 'type': 'string', 'in': 'path'}])
@marshal_with(PetSchema)
@use_kwargs({'breed': Arg(str)})
def get_pet(pet_id):
    return Pet('calici', 'cat')

docs.register(get_pet)

class MethodResourceMeta(ResourceMeta, flask.views.MethodViewType):
    pass

class MethodResource(six.with_metaclass(MethodResourceMeta, flask.views.MethodView)):
    methods = None

@doc(parameters=[{'name': 'pet_id', 'type': 'string', 'in': 'path'}])
class CatResource(MethodResource):

    @marshal_with(PetSchema)
    def get(self, pet_id):
        return Pet('calici', 'cat')

    @marshal_with(PetSchema)
    def put(self, pet_id):
        return Pet('calici', 'cat')

app.add_url_rule('/cat/<pet_id>', view_func=CatResource.as_view('CatResource'))
docs.register(CatResource)
