from flask_apispec import utils

class TestAnnotations:

    def test_equals(self):
        assert utils.Annotation() == utils.Annotation()

    def test_not_equals(self):
        assert utils.Annotation() != 7
        assert utils.Annotation() != utils.Annotation({'foo': 'bar'})
