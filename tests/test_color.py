import sys
from StringIO import StringIO
import unittest
from fragments import color


class TestColor(unittest.TestCase):

    def test_color(self):
        self.assertEquals(str(color.ColoredString('foo')), '\x1b[0m\x1b[37mfoo\x1b[0m')


class TestNotATTYColor(unittest.TestCase):

    def setUp(self):
        super(TestNotATTYColor, self).setUp()
        self._stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout = self._stdout
        super(TestNotATTYColor, self).tearDown()

    def test_notatty_color(self):
        self.assertEquals(str(color.ColoredString('foo')), 'foo')
