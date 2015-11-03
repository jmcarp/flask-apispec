# -*- coding: utf-8 -*-

import types

import flask
from apispec import APISpec

from flask_apispec import ResourceMeta
from flask_apispec.apidoc import ViewConverter, ResourceConverter

class FlaskSmore(object):
    """Flask-smore extension.

    Usage:

    .. code-block:: python

        app = Flask(__name__)
        app.config.update({
            'SMORE_APISPEC': APISpec(
                title='pets',
                version='v1',
                plugins=['apispec.ext.marshmallow'],
            ),
            'SMORE_SWAGGER_URL': '/swagger/',
        })
        docs = FlaskSmore(app)

        @app.route('/pet/<pet_id>')
        def get_pet(pet_id):
            return Pet.query.filter(Pet.id == pet_id).one()

        docs.register(get_pet)

    :param Flask app: App associated with API documentation
    :param APISpec spec: Smore specification associated with API documentation
    """
    def __init__(self, app):
        self.app = app
        self.view_converter = ViewConverter(self.app)
        self.resource_converter = ResourceConverter(self.app)
        self.spec = self.app.config.get('SMORE_APISPEC') or make_apispec()
        self.add_routes()

    def add_routes(self):
        blueprint = flask.Blueprint(
            'flask-smore',
            __name__,
            template_folder='./templates',
            static_folder='../node_modules/swagger-ui/dist',
            static_url_path='/flask-smore/static',
        )

        json_url = self.app.config.get('SMORE_SWAGGER_URL', '/swagger/')
        if json_url:
            blueprint.add_url_rule(json_url, 'swagger-json', self.swagger_json)

        ui_url = self.app.config.get('SMORE_SWAGGER_UI_URL', '/swagger-ui/')
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
