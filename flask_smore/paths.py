# -*- coding: utf-8 -*-

import re

import werkzeug.routing

PATH_RE = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')
def get_path(path):
    return PATH_RE.sub(r'{\1}', path)

CONVERTER_MAPPING = {
    werkzeug.routing.UnicodeConverter: ('string', None),
    werkzeug.routing.IntegerConverter: ('integer', 'int32'),
    werkzeug.routing.FloatConverter: ('number', 'float'),
}

DEFAULT_TYPE = ('string', None)

def rule_to_parameters(rule, overrides=None):
    overrides = overrides or {}
    return [
        argument_to_parameter(argument, rule, overrides.get(argument, {}))
        for argument in rule.arguments
    ]

def argument_to_parameter(argument, rule, override=None):
    param = {
        'in': 'path',
        'name': argument,
        'required': True,
    }
    type_, format_ = CONVERTER_MAPPING.get(type(rule._converters[argument]), DEFAULT_TYPE)
    param['type'] = type_
    if format_ is not None:
        param['format'] = format_
    if rule.defaults and argument in rule.defaults:
        param['default'] = rule.defaults[argument]
    param.update(override or {})
    return param
