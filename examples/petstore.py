# -*- coding: utf-8 -*-

import six
import marshmallow as ma

from flask_smore import ResourceMeta, marshal_with

class Pet:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class PetSchema(ma.Schema):
    class Meta:
        fields = ('name', 'type')

class PetResource(six.with_metaclass(ResourceMeta)):
    @marshal_with(PetSchema(), code=200)
    def get(self):
        return Pet('calici', 'cat')

class CatResource(PetResource):
    @marshal_with(PetSchema(), code=201)
    def get(self):
        return Pet('calici', 'cat'), 200
