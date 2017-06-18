# -*- coding: utf-8 -*-
from flask_apispec.views import ResourceMeta, MethodResource
from flask_apispec.annotations import doc, wrap_with, use_kwargs, marshal_with
from flask_apispec.extension import FlaskApiSpec
from flask_apispec.utils import Ref

__version__ = '0.4.0'
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
