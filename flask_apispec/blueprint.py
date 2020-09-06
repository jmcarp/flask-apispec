from flask import Blueprint as FlaskBlueprint
from flask.blueprints import BlueprintSetupState
from flask_apispec import MethodResource, FlaskApiSpec
import logging
import inspect

log = logging.getLogger(__name__)


class DocsBlueprintSetupState(BlueprintSetupState):

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        log.debug('add url rule:%s' % rule)
        doc_view_func = view_func
        if inspect.isclass(view_func) and issubclass(view_func, MethodResource):
            view_func = view_func.as_view(endpoint or view_func.__name__)
        super().add_url_rule(rule, endpoint, view_func, **options)
        docs = self.blueprint.docs
        log.debug('register %s' % doc_view_func.__name__)
        docs.register(doc_view_func, endpoint=endpoint, blueprint=self.blueprint.name)


class Blueprint(FlaskBlueprint):

    def __init__(self, docs: FlaskApiSpec, name: str, import_name: str, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.docs = docs

    def make_setup_state(self, app, options, first_registration=False):
        return DocsBlueprintSetupState(self, app, options, first_registration)