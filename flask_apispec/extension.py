# -*- coding: utf-8 -*-
import flask
import functools
import types
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

    def __init__(self, app=None):
        self._deferred = []
        self.app = app
        self.view_converter = None
        self.resource_converter = None
        self.spec = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.view_converter = ViewConverter(self.app)
        self.resource_converter = ResourceConverter(self.app)
        self.spec = self.app.config.get('APISPEC_SPEC') or \
                    make_apispec(self.app.config.get('APISPEC_TITLE', 'flask-apispec'),
                                 self.app.config.get('APISPEC_VERSION', 'v1'))

        self.add_swagger_routes()

        for deferred in self._deferred:
            deferred()

    def _defer(self, callable, *args, **kwargs):
        bound = functools.partial(callable, *args, **kwargs)
        self._deferred.append(bound)
        if self.app:
            bound()

    def add_swagger_routes(self):
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

    def register_existing_resources(self):
        for name, rule in self.app.view_functions.items():
            try:
                blueprint_name, _ = name.split('.')
            except ValueError:
                blueprint_name = None

            try:
                self.register(rule, blueprint=blueprint_name)
            except TypeError:
                pass

    def register(self, target, endpoint=None, blueprint=None,
                 resource_class_args=None, resource_class_kwargs=None):
        """Register a view.

        :param target: view function or view class.
        :param endpoint: (optional) endpoint name.
        :param blueprint: (optional) blueprint name.
        :param tuple resource_class_args: (optional) args to be forwarded to the
            view class constructor.
        :param dict resource_class_kwargs: (optional) kwargs to be forwarded to
            the view class constructor.
        """

        self._defer(self._register, target, endpoint, blueprint,
                    resource_class_args, resource_class_kwargs)

    def _register(self, target, endpoint=None, blueprint=None,
                  resource_class_args=None, resource_class_kwargs=None):
        """Register a view.

        :param target: view function or view class.
        :param endpoint: (optional) endpoint name.
        :param blueprint: (optional) blueprint name.
        :param tuple resource_class_args: (optional) args to be forwarded to the
            view class constructor.
        :param dict resource_class_kwargs: (optional) kwargs to be forwarded to
            the view class constructor.
        """
        if isinstance(target, types.FunctionType):
            paths = self.view_converter.convert(target, endpoint, blueprint)
        elif isinstance(target, ResourceMeta):
            paths = self.resource_converter.convert(
                target,
                endpoint,
                blueprint,
                resource_class_args=resource_class_args,
                resource_class_kwargs=resource_class_kwargs,
            )
        else:
            raise TypeError()
        for path in paths:
            self.spec.add_path(**path)


def make_apispec(title='flask-apispec', version='v1'):
    return APISpec(
        title=title,
        version=version,
        plugins=['apispec.ext.marshmallow'],
    )
