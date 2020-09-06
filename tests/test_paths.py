from flask_apispec.paths import rule_to_path, rule_to_params

def make_rule(app, path, **kwargs):
    @app.route(path, **kwargs)
    def view():
        pass
    return app.url_map._rules_by_endpoint['view'][0]

def make_param(in_location='path', **kwargs):
    ret = {'in': in_location, 'required': True}
    ret.update(kwargs)
    return ret

class TestPaths:

    def test_path(self, app):
        rule = make_rule(app, '/bands/<band_id>/')
        assert rule_to_path(rule) == '/bands/{band_id}/'

    def test_path_int(self, app):
        rule = make_rule(app, '/bands/<int:band_id>/')
        assert rule_to_path(rule) == '/bands/{band_id}/'

class TestPathParams:

    def test_params(self, app):
        rule = make_rule(app, '/<band_id>/')
        params = rule_to_params(rule)
        assert len(params) == 1
        expected = make_param(type='string', name='band_id')
        assert params[0] == expected

    def test_params_default(self, app):
        rule = make_rule(app, '/<band_id>/', defaults={'band_id': 'queen'})
        params = rule_to_params(rule)
        expected = make_param(type='string', name='band_id', default='queen')
        assert params[0] == expected

    def test_params_int(self, app):
        rule = make_rule(app, '/<int:band_id>/')
        params = rule_to_params(rule)
        expected = make_param(type='integer', format='int32', name='band_id')
        assert params[0] == expected

    def test_params_float(self, app):
        rule = make_rule(app, '/<float:band_id>/')
        params = rule_to_params(rule)
        expected = make_param(type='number', format='float', name='band_id')
        assert params[0] == expected

    def test_params_override(self, app):
        rule = make_rule(app, '/<band_id>/')
        overrides = {'band_id': {'description': 'the band id'}}
        params = rule_to_params(rule, overrides=overrides)
        expected = make_param(type='string', name='band_id', description='the band id')
        assert params[0] == expected
 
    def test_params_override_header(self, app):
        rule = make_rule(app, '/some_path/')
        overrides = {'Authorization': {'type': 'string', 'description': 'The authorization token', 'in': 'header', 'required': True}}
        params = rule_to_params(rule, overrides=overrides)
        expected = make_param(type='string', name='Authorization', in_location='header', description='The authorization token',
                              required=True)
        assert params[0] == expected
