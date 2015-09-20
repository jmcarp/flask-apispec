# -*- coding: utf-8 -*-

import types

import flask
from smore.apispec import APISpec

from flask_smore import ResourceMeta
from flask_smore.apidoc import ViewConverter, ResourceConverter

def make_apispec():
    return APISpec(
        title='flask-smore',
        version='v1',
        plugins=['smore.ext.marshmallow'],
    )

class FlaskSmore(object):
    """Flask-smore extension.

    Usage:

    .. code-block:: python

        app = Flask(__name__)
        app.config.update({
            'SMORE_APISPEC': APISpec(
                title='pets',
                version='v1',
                plugins=['smore.ext.marshmallow'],
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
        swagger_url = self.app.config.get('SMORE_SWAGGER_URL', '/swagger/')
        if swagger_url:
            self.app.add_url_rule(swagger_url, 'swagger_json', self.swagger_json)

    def swagger_json(self):
        return flask.jsonify(self.spec.to_dict())

    def register(self, target, endpoint=None, blueprint=None):
        if isinstance(target, types.FunctionType):
            paths = self.view_converter.convert(target, endpoint, blueprint)
        elif isinstance(target, ResourceMeta):
            paths = self.resource_converter.convert(target, endpoint, blueprint)
        else:
            raise TypeError()
        for path in paths:
            self.spec.add_path(**path)
