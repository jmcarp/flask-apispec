# -*- coding: utf-8 -*-

import re

import werkzeug.routing

PATH_RE = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')
def rule_to_path(rule):
    return PATH_RE.sub(r'{\1}', rule.rule)


CONVERTER_MAPPING = {
    werkzeug.routing.UnicodeConverter: ('string', None),
    werkzeug.routing.IntegerConverter: ('integer', 'int32'),
    werkzeug.routing.FloatConverter: ('number', 'float'),
}

DEFAULT_TYPE = ('string', None)

def rule_to_params(rule, overrides=None):
    overrides = overrides or {}
    return [
        argument_to_param(argument, rule, overrides.get(argument, {}))
        for argument in rule.arguments
    ]

def argument_to_param(argument, rule, override=None):
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
