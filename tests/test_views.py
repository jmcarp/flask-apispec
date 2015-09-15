# -*- coding: utf-8 -*-

from webargs import Arg
from flask import make_response

from flask_smore.utils import Ref
from flask_smore.views import MethodResource
from flask_smore import use_kwargs, marshal_with

from tests.fixtures import app, client, models, schemas  # noqa

class TestFunctionViews:

    def test_use_kwargs(self, app, client):
        @app.route('/')
        @use_kwargs({'name': Arg(str)})
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie'})
        assert res.json == {'name': 'freddie'}

    def test_use_kwargs_multiple(self, app, client):
        @app.route('/')
        @use_kwargs({'name': Arg(str)})
        @use_kwargs({'instrument': Arg(str)})
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie', 'instrument': 'vocals'})
        assert res.json == {'name': 'freddie', 'instrument': 'vocals'}

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
        @use_kwargs({'name': Arg(str), 'genre': Arg(str)})
        @marshal_with(schemas.BandSchema)
        def view(**kwargs):
            return models.Band(**kwargs)
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

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

    def test_kwargs_inheritance_ref(self, app, client, schemas):
        class BaseResource(MethodResource):
            @use_kwargs({'name': Arg(str)})
            def get(self, **kwargs):
                pass

        class ConcreteResource(BaseResource):
            kwargs = {'genre': Arg(str)}
            @use_kwargs(Ref('kwargs'))
            @marshal_with(schemas.BandSchema)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_kwargs_apply_false(self, app, client):
        class ConcreteResource(MethodResource):
            @use_kwargs({'genre': Arg(str)}, apply=False)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {}

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

    def test_kwargs_inheritance_false(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            @use_kwargs({'name': Arg(str), 'genre': Arg(str)})
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            @use_kwargs({'name': Arg(str)}, inherit=False)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen'}

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
                return make_response('', 204)

        app.add_url_rule('/<id>/', view_func=ConcreteResource.as_view('concrete'))
        res = client.delete('/5/')
        assert res.body == b''
