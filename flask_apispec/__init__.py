from flask_apispec.annotations import doc, marshal_with, use_kwargs, wrap_with
from flask_apispec.extension import FlaskApiSpec
from flask_apispec.utils import Ref
from flask_apispec.views import MethodResource, ResourceMeta

__version__ = '0.11.4'
__all__ = [
    'doc',
    'wrap_with',
    'use_kwargs',
    'marshal_with',
    'ResourceMeta',
    'MethodResource',
    'FlaskApiSpec',
    'Ref',
]
