import logging

import flask.views
import marshmallow as ma

from flask_apispec import FlaskApiSpec, MethodResource
from flask_apispec import doc, marshal_with, use_kwargs
from flask_apispec.blueprint import Blueprint

app = flask.Flask(__name__)
docs = FlaskApiSpec(app)

blueprint = Blueprint(docs, name='pet', import_name=__name__)

logging.basicConfig(level=logging.DEBUG)


class Pet:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class PetSchema(ma.Schema):
    name = ma.fields.Str()
    type = ma.fields.Str()


@blueprint.route('/pets/<pet_id>')
@doc(params={'pet_id': {'description': 'pet id'}})
@marshal_with(PetSchema)
@use_kwargs({'breed': ma.fields.Str()}, location='query')
def get_pet(pet_id,breed):
    return Pet('calici', 'cat')


@blueprint.route('/cat/<pet_id>')
@doc(
    tags=['pets'],
    params={'pet_id': {'description': 'the pet name'}},
)
class CatResource(MethodResource):

    @marshal_with(PetSchema)
    def get(self, pet_id):
        return Pet('calici', 'cat')

    @marshal_with(PetSchema)
    def put(self, pet_id):
        return Pet('calici', 'cat')


if __name__ == '__main__':
    app.register_blueprint(blueprint)
    app.run(debug=True)
