import pytest
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from marshmallow import fields, Schema
from flask import make_response

from flask_apispec.paths import rule_to_params
from flask_apispec.views import MethodResource
from flask_apispec import doc, use_kwargs, marshal_with
from flask_apispec.apidoc import ViewConverter, ResourceConverter

@pytest.fixture()
def marshmallow_plugin():
    return MarshmallowPlugin()

@pytest.fixture
def spec(marshmallow_plugin):
    return APISpec(
        title='title',
        version='v1',
        openapi_version='2.0',
        plugins=[marshmallow_plugin],
    )

@pytest.fixture
def spec_oapi3(marshmallow_plugin):
    return APISpec(
        title='title',
        version='v1',
        openapi_version='3.0',
        plugins=[marshmallow_plugin],
    )

@pytest.fixture()
def openapi(marshmallow_plugin):
    return marshmallow_plugin.converter

def ref_path(spec):
    if spec.openapi_version.version[0] < 3:
        return "#/definitions/"
    return "#/components/schemas/"

def test_error_if_spec_does_not_have_marshmallow_plugin(app):
    bad_spec = APISpec(
        title='title',
        version='v1',
        openapi_version='2.0',
        plugins=[],  # oh no! no MarshmallowPlugin
    )
    with pytest.raises(RuntimeError):
        ViewConverter(app=app, spec=bad_spec)
    with pytest.raises(RuntimeError):
        ResourceConverter(app=app, spec=bad_spec)

class TestFunctionView:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        @app.route('/bands/<int:band_id>/')
        @doc(tags=['band'])
        @use_kwargs({'name': fields.Str(missing='queen')}, location='query')
        @marshal_with(schemas.BandSchema, description='a band')
        def get_band(band_id):
            return models.Band(name='slowdive', genre='spacerock')
        return get_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app=app, spec=spec)
        paths = converter.convert(function_view)
        for path in paths:
            spec.path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['get_band'][0]
        expected = (
            [{
                'in': 'query',
                'name': 'name',
                'type': 'string',
                'required': False,
                'default': 'queen',
            }] + rule_to_params(rule)
        )
        assert params == expected

    def test_responses(self, schemas, path, openapi):
        response = path['get']['responses']['default']
        assert response['description'] == 'a band'
        assert response['schema'] == {'$ref': ref_path(openapi.spec) + 'Band'}

    def test_tags(self, path):
        assert path['get']['tags'] == ['band']

class TestFunctionView_OpenAPI3:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        @app.route('/bands/<int:band_id>/')
        @doc(tags=['band'])
        @use_kwargs({'name': fields.Str(missing='queen')}, locations=('query',))
        @marshal_with(schemas.BandSchema, description='a band', content_type='text/json')
        def get_band(band_id):
            return models.Band(name='slowdive', genre='spacerock')

        return get_band

    @pytest.fixture
    def path(self, app, spec_oapi3, function_view):
        converter = ViewConverter(app=app, spec=spec_oapi3)
        paths = converter.convert(function_view)
        for path in paths:
            spec_oapi3.path(**path)
        return spec_oapi3._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['get_band'][0]
        expected = (
                [{
                    'in': 'query',
                    'name': 'name',
                    'required': False,
                    'schema': {
                        'type': 'string',
                        'default': 'queen',
                    }
                }] + rule_to_params(rule)
        )
        assert params == expected

    def test_responses(self, schemas, path, openapi):
        response = path['get']['responses']['default']
        assert response['description'] == 'a band'
        assert response['content'] == {'text/json': {'schema': {'$ref': ref_path(openapi.spec) + 'Band'}}}

    def test_tags(self, path):
        assert path['get']['tags'] == ['band']

class TestArgSchema:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        class ArgSchema(Schema):
            name = fields.Str()

        @app.route('/bands/<int:band_id>/')
        @use_kwargs(ArgSchema, location='query')
        def get_band(**kwargs):
            return kwargs
        return get_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app=app, spec=spec)
        paths = converter.convert(function_view)
        for path in paths:
            spec.path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path, openapi):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['get_band'][0]
        expected = (
            openapi.schema2parameters(
                Schema.from_dict({'name': fields.Str()}), location='query') +
            rule_to_params(rule)
        )
        assert params == expected

class TestCallableAsArgSchema(TestArgSchema):

    @pytest.fixture
    def function_view(self, app, models, schemas):
        def schema_factory(request):
            class ArgSchema(Schema):
                name = fields.Str()

            return ArgSchema

        @app.route('/bands/<int:band_id>/')
        @use_kwargs(schema_factory, location='query')
        def get_band(**kwargs):
            return kwargs
        return get_band

class TestDeleteView:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        @app.route('/bands/<int:band_id>/', methods=['DELETE'])
        @marshal_with(None, code=204, description='a deleted band')
        def delete_band(band_id):
            return make_response('', 204)
        return delete_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app=app, spec=spec)
        paths = converter.convert(function_view)
        for path in paths:
            spec.path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_responses(self, schemas, path):
        response = path['delete']['responses']['204']
        assert response['description'] == 'a deleted band'
        assert response['schema'] == {}

class TestResourceView:

    @pytest.fixture
    def resource_view(self, app, models, schemas):
        @doc(tags=['band'])
        class BandResource(MethodResource):
            @use_kwargs({'name': fields.Str()}, location='query')
            @marshal_with(schemas.BandSchema, description='a band')
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze')

        app.add_url_rule('/bands/<band_id>/', view_func=BandResource.as_view('band'))
        return BandResource

    @pytest.fixture
    def path(self, app, spec, resource_view):
        converter = ResourceConverter(app=app, spec=spec)
        paths = converter.convert(resource_view, endpoint='band')
        for path in paths:
            spec.path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path, openapi):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['band'][0]
        expected = (
            [{'in': 'query', 'name': 'name', 'required': False, 'type': 'string'}] +
            rule_to_params(rule)
        )
        assert params == expected

    def test_responses(self, schemas, path, openapi):
        response = path['get']['responses']['default']
        assert response['description'] == 'a band'
        assert response['schema'] == {'$ref': ref_path(openapi.spec) + 'Band'}

    def test_tags(self, path):
        assert path['get']['tags'] == ['band']


class TestMultipleLocations:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        class QuerySchema(Schema):
            name = fields.Str()

        class BodySchema(Schema):
            address = fields.Str()

        @app.route('/bands/<int:band_id>/')
        @use_kwargs(QuerySchema, location='query')
        @use_kwargs(BodySchema, location='body')
        def get_band(**kwargs):
            return kwargs
        return get_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app=app, spec=spec)
        paths = converter.convert(function_view)
        for path in paths:
            spec.path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['get_band'][0]
        expected = (
            [{
                'in': 'query',
                'name': 'name',
                'required': False,
                'type': 'string'
            }, {
                'in': 'body',
                'name': 'body',
                'required': False,
                'schema': {'$ref': '#/definitions/Body'}
            }] + rule_to_params(rule)
        )
        assert params == expected

class TestGetFieldsNoLocationProvided:

    @pytest.fixture
    def function_view(self, app):
        @app.route('/bands/<int:band_id>/')
        @use_kwargs({'name': fields.Str(), 'address': fields.Str()})
        def get_band(**kwargs):
            return kwargs

        return get_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app=app, spec=spec)
        paths = converter.convert(function_view)
        for path in paths:
            spec.path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        assert {
            'in': 'body',
            'name': 'body',
            'required': False,
            'schema': {
                'properties': {
                    'address': {'type': 'string'},
                    'name': {'type': 'string'},
                },
                'type': 'object',
            },
        } in params

class TestGetFieldsBodyLocation(TestGetFieldsNoLocationProvided):

    @pytest.fixture
    def function_view(self, app):
        @app.route('/bands/<int:band_id>/')
        @use_kwargs({'name': fields.Str(required=True), 'address': fields.Str(), 'email': fields.Str(required=True)})
        def get_band(**kwargs):
            return kwargs

        return get_band

    def test_params(self, app, path):
        params = path['get']['parameters']
        assert {
            'in': 'body',
            'name': 'body',
            'required': False,
            'schema': {
                'properties': {
                    'address': {'type': 'string'},
                    'name': {'type': 'string'},
                    'email': {'type': 'string'},
                },
                'required': ["name", "email"],
                'type': 'object',
            },
        } in params

class TestSchemaNoLocationProvided:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        class BodySchema(Schema):
            address = fields.Str()

        @app.route('/bands/<int:band_id>/')
        @use_kwargs(BodySchema)
        def get_band(**kwargs):
            return kwargs
        return get_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app=app, spec=spec)
        paths = converter.convert(function_view)
        for path in paths:
            spec.path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        assert {'name': 'body', 'in': 'body', 'required': False,
                'schema': {'$ref': '#/definitions/Body'}} in params
