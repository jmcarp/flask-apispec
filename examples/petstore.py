# -*- coding: utf-8 -*-

import six
from webargs import Arg
import marshmallow as ma

from flask_smore import ResourceMeta, Ref, marshal_with, use_kwargs

class Pet:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class PetSchema(ma.Schema):
    class Meta:
        fields = ('name', 'type')

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
