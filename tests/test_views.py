import json

from flask import make_response
from marshmallow import fields, Schema, post_load, EXCLUDE

from flask_apispec.utils import Ref
from flask_apispec.views import MethodResource
from flask_apispec import doc, use_kwargs, marshal_with


# All the following schemas are set with unknown = EXCLUDE
# because part of a multiple schema input.
# This way none of them will raise errors for unknown fields handled by others
class NameSchema(Schema):
    name = fields.Str()

    class Meta:
        unknown = EXCLUDE


class NameGenreSchema(Schema):
    name = fields.Str()
    genre = fields.Str()

    class Meta:
        unknown = EXCLUDE


class GenreSchema(Schema):
    genre = fields.Str()

    class Meta:
        unknown = EXCLUDE


class InstrumentSchema(Schema):
    instrument = fields.Str()

    class Meta:
        unknown = EXCLUDE

class TestFunctionViews:

    def test_use_kwargs(self, app, client):
        @app.route('/')
        @use_kwargs({'name': fields.Str()}, location='querystring')
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie'})
        assert res.json == {'name': 'freddie'}

    def test_use_kwargs_nolocation(self, app, client):
        @app.route('/')
        @use_kwargs({'name': fields.Str()})
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie'})
        # default location is 'json', i.e. no kwargs will be received here
        assert res.json == {}

    def test_view_returning_tuple(self, app, client):
        @app.route('/all')
        @use_kwargs({'name': fields.Str()}, location='querystring')
        def all(**kwargs):
            return kwargs, 202, {'x-msg': 'test'}

        @app.route('/headers')
        @use_kwargs({'name': fields.Str()}, location='querystring')
        def view_headers(**kwargs):
            return kwargs, {'x-msg': 'test'}

        @app.route('/code')
        @use_kwargs({'name': fields.Str()}, location='querystring')
        def view_code(**kwargs):
            return kwargs, 202

        res_all = client.get('/all', {'name': 'freddie'})
        assert res_all.json == {'name': 'freddie'}
        assert res_all.status_code == 202
        assert res_all.headers.get('x-msg') == 'test'

        res_headers = client.get('/headers', {'name': 'freddie'})
        assert res_headers.json == {'name': 'freddie'}
        assert res_headers.status_code == 200
        assert res_headers.headers.get('x-msg') == 'test'

        res_code = client.get('/code', {'name': 'freddie'})
        assert res_code.json == {'name': 'freddie'}
        assert res_code.status_code == 202
        assert 'x-msg' not in res_code.headers

    def test_use_kwargs_schema(self, app, client):
        class ArgSchema(Schema):
            name = fields.Str()

        @app.route('/')
        @use_kwargs(ArgSchema, location='querystring')
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie'})
        assert res.json == {'name': 'freddie'}

    def test_use_kwargs_schema_with_post_load(self, app, client):
        class User:
            def __init__(self, name):
                self.name = name

            def update(self, name):
                self.name = name

        class ArgSchema(Schema):
            name = fields.Str()

            @post_load
            def make_object(self, data, **kwargs):
                return User(**data)

        @app.route('/', methods=('POST', ))
        @use_kwargs(ArgSchema(), location='json_or_form')
        def view(user):
            assert isinstance(user, User)
            return {'name': user.name}

        data = {'name': 'freddie'}
        res = client.post('/', data)
        assert res.json == data

    def test_use_kwargs_schema_many(self, app, client):
        class ArgSchema(Schema):
            name = fields.Str()

        @app.route('/', methods=('POST',))
        @use_kwargs(ArgSchema(many=True), location='json')
        def view(*args):
            return list(args)
        data = [{'name': 'freddie'}, {'name': 'john'}]
        res = client.post('/', json.dumps(data), content_type='application/json')
        assert res.json == data

    def test_use_kwargs_multiple(self, app, client):
        @app.route('/')
        @use_kwargs(NameSchema, location='querystring')
        @use_kwargs(InstrumentSchema, location='querystring')
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie', 'instrument': 'vocals'})
        assert res.json == {'name': 'freddie', 'instrument': 'vocals'}

    def test_use_kwargs_callable_as_schema(self, app, client):
        def schema_factory(request):
            assert request.method == 'GET'
            assert request.path == '/'

            class ArgSchema(Schema):
                name = fields.Str()

            return ArgSchema

        @app.route('/')
        @use_kwargs(schema_factory, location='querystring')
        def view(**kwargs):
            return kwargs
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

    def test_integration(self, app, client, models, schemas):
        @app.route('/')
        @use_kwargs(
            {'name': fields.Str(), 'genre': fields.Str()},
            location='querystring'
        )
        @marshal_with(schemas.BandSchema)
        def view(**kwargs):
            return models.Band(**kwargs)
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

class TestClassViews:

    def test_inheritance_unidirectional(self, app, client):
        @doc(tags=['base'])
        class BaseResource(MethodResource):
            @doc(description='parent')
            def get(self, **kwargs):
                pass

        @doc(tags=['child'])
        class ChildResource(BaseResource):
            @doc(description='child')
            def get(self, **kwargs):
                return kwargs

        assert not any(MethodResource.__apispec__.values())

        assert BaseResource.__apispec__['docs'][0].options[0]['tags'] == ['base']
        assert ChildResource.__apispec__['docs'][0].options[0]['tags'] == ['child']

        assert BaseResource.get.__apispec__['docs'][0].options[0]['description'] == 'parent'
        assert ChildResource.get.__apispec__['docs'][0].options[0]['description'] == 'child'

    def test_inheritance_only_http_methods(self, app):
        @use_kwargs({'genre': fields.Str()})
        class ConcreteResource(MethodResource):
            def _helper(self, **kwargs):
                return kwargs

        with app.test_request_context():
            resource = ConcreteResource()
            assert resource._helper() == {}

    def test_kwargs_inheritance(self, app, client):
        class BaseResource(MethodResource):
            @use_kwargs(NameSchema, location='querystring')
            def get(self, **kwargs):
                pass

        class ConcreteResource(BaseResource):
            @use_kwargs(GenreSchema, location='querystring')
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_kwargs_inheritance_ref(self, app, client, schemas):
        class BaseResource(MethodResource):
            @use_kwargs(NameSchema, location='querystring')
            def get(self, **kwargs):
                pass

        class ConcreteResource(BaseResource):
            kwargs = GenreSchema

            @use_kwargs(Ref('kwargs'), location='querystring')
            @marshal_with(schemas.BandSchema)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_kwargs_inheritance_false(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            @use_kwargs(NameGenreSchema, location='querystring')
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            @use_kwargs(NameSchema, inherit=False, location='querystring')
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen'}

    def test_kwargs_apply_false(self, app, client):
        class ConcreteResource(MethodResource):
            @use_kwargs(GenreSchema, apply=False)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {}

    def test_schemas_class(self, app, client, models, schemas):
        @marshal_with(schemas.BandSchema)
        class ConcreteResource(MethodResource):
            @marshal_with(schemas.BandSchema(only=('genre', )), code=201)
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

    def test_schemas_class_inheritance(self, app, client, models, schemas):
        @marshal_with(schemas.BandSchema(only=('genre', )))
        class BaseResource(MethodResource):
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

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

    def test_schemas_inheritance_false(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            @marshal_with(schemas.BandSchema, code=201)
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            @marshal_with(schemas.BandSchema(only=('genre', )), inherit=False)
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

    def test_schemas_apply_false(self, app, client, models, schemas):
        class ConcreteResource(MethodResource):
            @marshal_with(schemas.BandSchema, apply=False)
            def get(self, **kwargs):
                return {'genre': 'spacerock'}

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'spacerock'}

    def test_schemas_none(self, app, client, models, schemas):
        class ConcreteResource(MethodResource):
            @marshal_with(None, code=204)
            def delete(self, **kwargs):
                response = make_response('', 204)
                response.headers = {}
                return response

        app.add_url_rule('/<id>/', view_func=ConcreteResource.as_view('concrete'))
        res = client.delete('/5/')
        assert res.body == b''
