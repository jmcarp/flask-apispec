import marshmallow as ma

from flask_apispec import ResourceMeta, Ref, doc, marshal_with, use_kwargs


class Pet:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class PetSchema(ma.Schema):
    name = ma.fields.Str()
    type = ma.fields.Str()


class PetResource(metaclass=ResourceMeta):
    @use_kwargs({
        'category': ma.fields.Str(),
        'name': ma.fields.Str(),
    })
    @marshal_with(PetSchema(), code=200)
    def get(self):
        return Pet('calici', 'cat')


class CatResource(PetResource):
    @use_kwargs({'category': ma.fields.Int()})
    @marshal_with(PetSchema(), code=201)
    def get(self):
        return Pet('calici', 'cat'), 200

###

class CrudResource(metaclass=ResourceMeta):

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

from flask_apispec import FlaskApiSpec

app = flask.Flask(__name__)
docs = FlaskApiSpec(app)

@app.route('/pets/<pet_id>')
@doc(params={'pet_id': {'description': 'pet id'}})
@marshal_with(PetSchema)
@use_kwargs({'breed': ma.fields.Str()})
def get_pet(pet_id):
    return Pet('calici', 'cat')

docs.register(get_pet)

class MethodResourceMeta(ResourceMeta, flask.views.MethodViewType):
    pass

class MethodResource(flask.views.MethodView, metaclass=MethodResourceMeta):
    methods = None

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

app.add_url_rule('/cat/<pet_id>', view_func=CatResource.as_view('CatResource'))
docs.register(CatResource, endpoint='CatResource')

if __name__ == '__main__':
    app.run(debug=True)
