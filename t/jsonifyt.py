
import unittest

from lilac.jsonify import dumps, jsonify


class TestJsonify(unittest.TestCase):

    def test_custom_json(self):

        class Dummy(object):

            def as_json(self):
                return [1, 3, 3]

        self.assertEqual(dumps(Dummy()), '[1, 3, 3]')