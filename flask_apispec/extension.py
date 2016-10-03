# -*- coding: utf-8 -*-

import types

import flask
from apispec import APISpec

from flask_apispec import ResourceMeta
from flask_apispec.apidoc import ViewConverter, ResourceConverter

class FlaskApiSpec(object):
    """Flask-apispec extension.

    Usage:

    .. code-block:: python

        app = Flask(__name__)
        app.config.update({
            'APISPEC_SPEC': APISpec(
                title='pets',
                version='v1',
                plugins=['apispec.ext.marshmallow'],
            ),
            'APISPEC_SWAGGER_URL': '/swagger/',
        })
        docs = FlaskApiSpec(app)

        @app.route('/pet/<pet_id>')
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

        docs.register(get_pet)

    :param Flask app: App associated with API documentation
    :param APISpec spec: apispec specification associated with API documentation
    """
    def __init__(self, app):
        self.app = app
        self.view_converter = ViewConverter(self.app)
        self.resource_converter = ResourceConverter(self.app)
        self.spec = self.app.config.get('APISPEC_SPEC') or make_apispec()
        self.add_routes()

    def add_routes(self):
        blueprint = flask.Blueprint(
            'flask-apispec',
            __name__,
            static_folder='./static',
            template_folder='./templates',
            static_url_path='/flask-apispec/static',
        )

        json_url = self.app.config.get('APISPEC_SWAGGER_URL', '/swagger/')
        if json_url:
            blueprint.add_url_rule(json_url, 'swagger-json', self.swagger_json)

        ui_url = self.app.config.get('APISPEC_SWAGGER_UI_URL', '/swagger-ui/')
        if ui_url:
            blueprint.add_url_rule(ui_url, 'swagger-ui', self.swagger_ui)

        self.app.register_blueprint(blueprint)

    def swagger_json(self):
        return flask.jsonify(self.spec.to_dict())

    def swagger_ui(self):
        return flask.render_template('swagger-ui.html')

    def register(self, target, endpoint=None, blueprint=None):
        if isinstance(target, types.FunctionType):
            paths = self.view_converter.convert(target, endpoint, blueprint)
        elif isinstance(target, ResourceMeta):
            paths = self.resource_converter.convert(target, endpoint, blueprint)
        else:
            raise TypeError()
        for path in paths:
            self.spec.add_path(**path)

def make_apispec():
    return APISpec(
        title='flask-apispec',
        version='v1',
        plugins=['apispec.ext.marshmallow'],
    )
