# -*- coding: utf-8 -*-

import pytest
from smore import swagger
from smore.apispec import APISpec
from marshmallow import fields, Schema
from flask import make_response

from flask_smore.paths import rule_to_params
from flask_smore.views import MethodResource
from flask_smore import doc, use_kwargs, marshal_with
from flask_smore.apidoc import ViewConverter, ResourceConverter

from tests.fixtures import app, models, schemas  # noqa

@pytest.fixture
def spec():
    return APISpec(
        title='title',
        version='v1',
        plugins=['smore.ext.marshmallow'],
    )

class TestFunctionView:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        @app.route('/bands/<int:band_id>/')
        @doc(tags=['band'])
        @use_kwargs({'name': fields.Str()})
        @marshal_with(schemas.BandSchema, description='a band')
        def get_band(band_id):
            return models.Band(name='slowdive', genre='spacerock')
        return get_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app)
        paths = converter.convert(function_view)
        for path in paths:
            spec.add_path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['get_band'][0]
        expected = (
            swagger.fields2parameters({'name': fields.Str()}, default_in='query') +
            rule_to_params(rule)
        )
        assert params == expected

    def test_responses(self, schemas, path):
        response = path['get']['responses']['default']
        assert response['description'] == 'a band'
        assert response['schema'] == swagger.schema2jsonschema(schemas.BandSchema)

    def test_tags(self, path):
        assert path['get']['tags'] == ['band']

class TestArgSchema:

    @pytest.fixture
    def function_view(self, app, models, schemas):
        class ArgSchema(Schema):
            name = fields.Str()

        @app.route('/bands/<int:band_id>/')
        @use_kwargs(ArgSchema)
        def get_band(**kwargs):
            return kwargs
        return get_band

    @pytest.fixture
    def path(self, app, spec, function_view):
        converter = ViewConverter(app)
        paths = converter.convert(function_view)
        for path in paths:
            spec.add_path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['get_band'][0]
        expected = (
            swagger.fields2parameters({'name': fields.Str()}, default_in='query') +
            rule_to_params(rule)
        )
        assert params == expected

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
        converter = ViewConverter(app)
        paths = converter.convert(function_view)
        for path in paths:
            spec.add_path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_responses(self, schemas, path):
        response = path['delete']['responses'][204]
        assert response['description'] == 'a deleted band'
        assert response['schema'] == {}

class TestResourceView:

    @pytest.fixture
    def resource_view(self, app, models, schemas):
        @doc(tags=['band'])
        class BandResource(MethodResource):
            @use_kwargs({'name': fields.Str()})
            @marshal_with(schemas.BandSchema, description='a band')
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze')

        app.add_url_rule('/bands/<band_id>/', view_func=BandResource.as_view('band'))
        return BandResource

    @pytest.fixture
    def path(self, app, spec, resource_view):
        converter = ResourceConverter(app)
        paths = converter.convert(resource_view, endpoint='band')
        for path in paths:
            spec.add_path(**path)
        return spec._paths['/bands/{band_id}/']

    def test_params(self, app, path):
        params = path['get']['parameters']
        rule = app.url_map._rules_by_endpoint['band'][0]
        expected = (
            swagger.fields2parameters({'name': fields.Str()}, default_in='query') +
            rule_to_params(rule)
        )
        assert params == expected

    def test_responses(self, schemas, path):
        response = path['get']['responses']['default']
        assert response['description'] == 'a band'
        assert response['schema'] == swagger.schema2jsonschema(schemas.BandSchema)

    def test_tags(self, path):
        assert path['get']['tags'] == ['band']
