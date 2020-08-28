import pytest
from flask import Blueprint

from flask_apispec import doc
from flask_apispec.extension import FlaskApiSpec
from flask_apispec.views import MethodResource


@pytest.fixture
def docs(app):
    return FlaskApiSpec(app)

class TestExtension:
    def test_deferred_register(self, app):
        blueprint = Blueprint('test', __name__)
        docs = FlaskApiSpec()

        @doc(tags=['band'])
        class BandResource(MethodResource):
            def get(self, **kwargs):
                return 'slowdive'

        blueprint.add_url_rule('/bands/<band_id>/', view_func=BandResource.as_view('band'))
        docs.register(BandResource, endpoint='band', blueprint=blueprint.name)

        app.register_blueprint(blueprint)
        docs.init_app(app)

        assert '/bands/{band_id}/' in docs.spec._paths

    def test_register_function(self, app, docs):
        @app.route('/bands/<int:band_id>/')
        @doc(tags=['band'])
        def get_band(band_id):
            return 'queen'
        docs.register(get_band)
        assert '/bands/{band_id}/' in docs.spec._paths

    def test_register_resource(self, app, docs):
        @doc(tags=['band'])
        class BandResource(MethodResource):
            def get(self, **kwargs):
                return 'slowdive'
        app.add_url_rule('/bands/<band_id>/', view_func=BandResource.as_view('band'))
        docs.register(BandResource, endpoint='band')
        assert '/bands/{band_id}/' in docs.spec._paths

    def test_register_resource_with_constructor_args(self, app, docs):
        @doc(tags=['band'])
        class BandResource(MethodResource):
            def __init__(self, arg_one, arg_two):
                pass

            def get(self, **kwargs):
                return 'kraftwerk'

        app.add_url_rule('/bands/<band_id>/',
                         view_func=BandResource.as_view('band', True, arg_two=False))
        docs.register(BandResource, endpoint='band',
                      resource_class_args=(True, ),
                      resource_class_kwargs={'arg_two': True})
        assert '/bands/{band_id}/' in docs.spec._paths

    def test_register_existing_resources(self, app, docs):
        @app.route('/bands/<int:band_id>/')
        @doc(tags=['band'])
        def get_band(band_id):
            return 'queen'
        docs.register_existing_resources()
        assert '/bands/{band_id}/' in docs.spec._paths

    def test_serve_swagger(self, app, docs, client):
        res = client.get('/swagger/')
        assert res.json == docs.spec.to_dict()

    def test_serve_swagger_custom_url(self, app, client):
        app.config['APISPEC_SWAGGER_URL'] = '/swagger.json'
        docs = FlaskApiSpec(app)
        res = client.get('/swagger.json')
        assert res.json == docs.spec.to_dict()

    def test_serve_swagger_ui(self, app, docs, client):
        client.get('/swagger-ui/')

    def test_serve_swagger_ui_custom_url(self, app, client):
        app.config['APISPEC_SWAGGER_UI_URL'] = '/swagger-ui.html'
        FlaskApiSpec(app)
        client.get('/swagger-ui.html')

    def test_apispec_config(self, app):
        app.config['APISPEC_TITLE'] = 'test-extension'
        app.config['APISPEC_VERSION'] = '2.1'
        app.config['APISPEC_OAS_VERSION'] = '2.0'
        docs = FlaskApiSpec(app)

        assert docs.spec.title == 'test-extension'
        assert docs.spec.version == '2.1'
        assert docs.spec.openapi_version == '2.0'
