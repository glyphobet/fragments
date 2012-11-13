# -*- coding: utf-8
from __future__ import unicode_literals

import os
import sys
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import unittest
from fragments import color

class FakeTTY(StringIO):
    def isatty(self):
        return True


class TestColor(unittest.TestCase):

    def setUp(self):
        super(TestColor, self).setUp()
        self._stdout = sys.stdout
        sys.stdout = FakeTTY()

    def tearDown(self):
        sys.stdout = self._stdout
        super(TestColor, self).tearDown()

    def test_color(self):
        self.assertTrue(sys.stdout.isatty())
        self.assertEquals(color.ColoredString('foo').colorize(), '\x1b[0m\x1b[37mfoo\x1b[0m')

    def test_not_colorblind(self):
        old_colorblind = os.getenv('COLORBLIND')
        try:
            if old_colorblind is not None:
                del os.environ['COLORBLIND']
            self.assertEquals(color.Added('foo').colorize(), '\x1b[0m\x1b[32mfoo\x1b[0m')
        finally:
            if old_colorblind is not None:
                os.environ['COLORBLIND'] = old_colorblind

    def test_colorblind(self):
        old_colorblind = os.getenv('COLORBLIND')
        try:
            os.environ['COLORBLIND'] = 'protan'
            self.assertEquals(color.Added('foo').colorize(), '\x1b[0m\x1b[34mfoo\x1b[0m')
        finally:
            if old_colorblind is not None:
                os.environ['COLORBLIND'] = old_colorblind
            else:
                del os.environ['COLORBLIND']


class TestNotATTYColor(unittest.TestCase):

    def setUp(self):
        super(TestNotATTYColor, self).setUp()
        self._stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout = self._stdout
        super(TestNotATTYColor, self).tearDown()

    def test_notatty_color(self):
        self.assertEquals(color.ColoredString('foo').colorize(), 'foo')
