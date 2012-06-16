# -*- coding: utf-8
from __future__ import unicode_literals

# This code is based on code from
#   http://revctrl.org/PreciseCodevilleMerge?action=AttachFile
# That code was in turn based on BSD-licensed code from the Codeville distributed version control system

import unittest

from fragments.precisecodevillemerge import Weave, unique_lcs, recurse_matches

class TestWeave(unittest.TestCase):
    def test_unique_lcs(self):
        self.assertEquals(unique_lcs('', ''), [])
        self.assertEquals(unique_lcs('a', 'a'), [(0, 0)])
        self.assertEquals(unique_lcs('a', 'b'), [])
        self.assertEquals(unique_lcs('ab', 'ab'), [(0, 0), (1, 1)])
        self.assertEquals(unique_lcs('abcde', 'cdeab'), [(2, 0), (3, 1), (4, 2)])
        self.assertEquals(unique_lcs('cdeab', 'abcde'), [(0, 2), (1, 3), (2, 4)])
        self.assertEquals(unique_lcs('abXde', 'abYde'), [(0, 0), (1, 1), (3, 3), (4, 4)])
        self.assertEquals(unique_lcs('acbac', 'abc'), [(2, 1)])

    def test_recurse_matches(self):
        a1 = []
        recurse_matches(['a', None, 'b', None, 'c'], ['a', 'a', 'b', 'c', 'c'], 5, 5, a1, 10)
        self.assertEquals(a1, [(0, 0), (2, 2), (4, 4)])
        a2 = []
        recurse_matches(['a', 'c', 'b', 'a', 'c'], ['a', 'b', 'c'], 5, 3, a2, 10)
        self.assertEquals( a2, [(0, 0), (2, 1), (4, 2)])

    def test_weave1(self):
        w = Weave()
        w.add_revision(1, ['a', 'b'], [])
        self.assertEquals(w.retrieve_revision(1), ['a', 'b'])
        w.add_revision(2, ['a', 'x', 'b'], [1])
        self.assertEquals(w.retrieve_revision(2), ['a', 'x', 'b'])
        w.add_revision(3, ['a', 'y', 'b'], [1])
        self.assertEquals(w.retrieve_revision(3), ['a', 'y', 'b'])
        self.assertEquals(w.merge(2, 3), ['a', (['x'], ['y']), 'b'])
        w.add_revision(4, ['a', 'x', 'b'], [1])
        w.add_revision(5, ['a', 'z', 'b'], [4])
        self.assertEquals(w.merge(2, 5), ['a', 'z', 'b'])

    def test_weave2(self):
        w = Weave()
        w.add_revision(1, ['b'], [])
        self.assertEquals(w.retrieve_revision(1), ['b'])
        w.add_revision(2, ['x', 'b'], [1])
        self.assertEquals(w.retrieve_revision(2), ['x', 'b'])
        w.add_revision(3, ['y', 'b'], [1])
        self.assertEquals(w.retrieve_revision(3), ['y', 'b'])
        self.assertEquals(w.merge(2, 3), [(['x'], ['y']), 'b'])
        w.add_revision(4, ['x', 'b'], [1])
        w.add_revision(5, ['z', 'b'], [4])
        self.assertEquals(w.merge(2, 5), ['z', 'b'])

    def test_weave3(self):
        w = Weave()
        w.add_revision(1, ['a'], [])
        self.assertEquals(w.retrieve_revision(1), ['a'])
        w.add_revision(2, ['a', 'x'], [1])
        self.assertEquals(w.retrieve_revision(2), ['a', 'x'])
        w.add_revision(3, ['a', 'y'], [1])
        self.assertEquals(w.retrieve_revision(3), ['a', 'y'])
        self.assertEquals(w.merge(2, 3), ['a', (['x'], ['y'])])
        w.add_revision(4, ['a', 'x'], [1])
        w.add_revision(5, ['a', 'z'], [4])
        self.assertEquals(w.merge(2, 5), ['a', 'z'])

    def test_weave4(self):
        w = Weave()
        w.add_revision(1, [], [])
        self.assertEquals(w.retrieve_revision(1), [])
        w.add_revision(2, ['x'], [1])
        self.assertEquals(w.retrieve_revision(2), ['x'])
        w.add_revision(3, ['y'], [1])
        self.assertEquals(w.retrieve_revision(3), ['y'])
        self.assertEquals(w.merge(2, 3), [(['x'], ['y'])])
        w.add_revision(4, ['x'], [1])
        w.add_revision(5, ['z'], [4])
        self.assertEquals(w.merge(2, 5), ['z'])

    def test_weave5(self):
        w = Weave()
        w.add_revision(1, ['a', 'b'], [])
        w.add_revision(2, ['a', 'c', 'b'], [1])
        w.add_revision(3, ['a', 'b'], [2])
        w.add_revision(4, ['a', 'd', 'b'], [1])
        self.assertEquals(w.merge(2, 4), ['a', (['c'], ['d']), 'b'])
        self.assertEquals(w.merge(3, 4), ['a', ([], ['d']), 'b'])
        w.add_revision(5, ['a', 'b'], [4])
        self.assertEquals(w.merge(4, 5), ['a', 'b'])

    def test_weave6(self):
        w = Weave()
        w.add_revision(1, ['b'], [])
        w.add_revision(2, ['c', 'b'], [1])
        w.add_revision(3, ['b'], [2])
        w.add_revision(4, ['d', 'b'], [1])
        self.assertEquals(w.merge(2, 4), [(['c'], ['d']), 'b'])
        self.assertEquals(w.merge(3, 4), [([], ['d']), 'b'])
        w.add_revision(5, ['b'], [4])
        self.assertEquals(w.merge(4, 5), ['b'])

    def test_weave7(self):
        w = Weave()
        w.add_revision(1, ['a'], [])
        w.add_revision(2, ['a', 'c'], [1])
        w.add_revision(3, ['a'], [2])
        w.add_revision(4, ['a', 'd'], [1])
        self.assertEquals(w.merge(2, 4), ['a', (['c'], ['d'])])
        self.assertEquals(w.merge(3, 4), ['a', ([], ['d'])])
        w.add_revision(5, ['a'], [4])
        self.assertEquals(w.merge(4, 5), ['a'])

    def test_weave8(self):
        w = Weave()
        w.add_revision(1, [], [])
        w.add_revision(2, ['c'], [1])
        w.add_revision(3, [], [2])
        w.add_revision(4, ['d'], [1])
        self.assertEquals(w.merge(2, 4), [(['c'], ['d'])])
        self.assertEquals(w.merge(3, 4), [([], ['d'])])
        w.add_revision(5, [], [4])
        self.assertEquals(w.merge(4, 5), [])

    def test_weave9(self):
        w = Weave()
        w.add_revision(1, ['a', 'b', 'c', 'd', 'e'], [])
        w.add_revision(2, ['a', 'x', 'c', 'd', 'e'], [1])
        w.add_revision(3, ['a', 'e'], [1])
        w.add_revision(4, ['a', 'b', 'c', 'd', 'e'], [3])
        self.assertEquals(w.merge(2, 4), ['a', (['x'], ['b']), 'c', 'd', 'e'])

    def test_weave10(self):
        w = Weave()
        w.add_revision(1, ['b', 'c', 'd', 'e'], [])
        w.add_revision(2, ['x', 'c', 'd', 'e'], [1])
        w.add_revision(3, ['e'], [1])
        w.add_revision(4, ['b', 'c', 'd', 'e'], [3])
        self.assertEquals(w.merge(2, 4), [(['x'], ['b']), 'c', 'd', 'e'])

    def test_weave11(self):
        w = Weave()
        w.add_revision(1, ['a', 'b', 'c', 'd'], [])
        w.add_revision(2, ['a', 'x', 'c', 'd'], [1])
        w.add_revision(3, ['a'], [1])
        w.add_revision(4, ['a', 'b', 'c', 'd'], [3])
        self.assertEquals(w.merge(2, 4), ['a', (['x'], ['b']), 'c', 'd'])

    def test_weave12(self):
        w = Weave()
        w.add_revision(1, ['b', 'c', 'd'], [])
        w.add_revision(2, ['x', 'c', 'd'], [1])
        w.add_revision(3, [], [1])
        w.add_revision(4, ['b', 'c', 'd'], [3])
        self.assertEquals(w.merge(2, 4), [(['x'], ['b']), 'c', 'd'])

    def test_weave13(self):
        w = Weave()
        w.add_revision(1, ['a', 'b'], [])
        w.add_revision(2, ['a', 'c', 'b'], [1])
        w.add_revision(3, ['a', 'd', 'b'], [1])
        w.add_revision(4, ['a', 'c', 'd', 'b'], [2, 3])
        w.add_revision(5, ['a', 'd', 'c', 'b'], [2, 3])
        self.assertEquals(w.merge(4, 5), ['a', (['c'], []), 'd', 'c', 'b'])

    def test_weave14(self):
        w = Weave()
        w.add_revision(1, ['b'], [])
        w.add_revision(2, ['c', 'b'], [1])
        w.add_revision(3, ['d', 'b'], [1])
        w.add_revision(4, ['c', 'd', 'b'], [2, 3])
        w.add_revision(5, ['d', 'c', 'b'], [2, 3])
        self.assertEquals(w.merge(4, 5), [(['c'], []), 'd', 'c', 'b'])

    def test_weave15(self):
        w = Weave()
        w.add_revision(1, ['a'], [])
        w.add_revision(2, ['a', 'c'], [1])
        w.add_revision(3, ['a', 'd'], [1])
        w.add_revision(4, ['a', 'c', 'd'], [2, 3])
        w.add_revision(5, ['a', 'd', 'c'], [2, 3])
        self.assertEquals(w.merge(4, 5), ['a', (['c'], []), 'd', 'c'])

    def test_weave16(self):
        w = Weave()
        w.add_revision(1, [], [])
        w.add_revision(2, ['c'], [1])
        w.add_revision(3, ['d'], [1])
        w.add_revision(4, ['c', 'd'], [2, 3])
        w.add_revision(5, ['d', 'c'], [2, 3])
        self.assertEquals(w.merge(4, 5), [(['c'], []), 'd', 'c'])

    def test_weave17(self):
        w = Weave()
        w.add_revision(1, ['a', 'b'], [])
        w.add_revision(2, ['a', 'f', 'y', 'y', 'f', 'b'], [1])
        w.add_revision(3, ['a', 'y', 'b'], [1])
        w.add_revision(4, ['a', 'p', 'y', 'p', 'b'], [3])
        w.add_revision(5, ['a', 'q', 'y', 'q', 'b'], [3])
        self.assertEquals(w.merge(4, 5), ['a', (['p'], ['q']), 'y', (['p'], ['q']), 'b'])

    def test_weave18(self):
        w = Weave()
        w.add_revision(1, [], [])
        w.add_revision(2, ['f', 'y', 'y', 'f'], [1])
        w.add_revision(3, ['y'], [1])
        w.add_revision(4, ['p', 'y', 'p'], [3])
        w.add_revision(5, ['q', 'y', 'q'], [3])
        self.assertEquals(w.merge(4, 5), [(['p'], ['q']), 'y', (['p'], ['q'])])

    def test_weave19(self):
        w = Weave()
        w.add_revision(1, ['a'], [])
        w.add_revision(2, ['a', 'f', 'y', 'y', 'f'], [1])
        w.add_revision(3, ['a', 'y'], [1])
        w.add_revision(4, ['a', 'p', 'y', 'p'], [3])
        w.add_revision(5, ['a', 'q', 'y', 'q'], [3])
        self.assertEquals(w.merge(4, 5), ['a', (['p'], ['q']), 'y', (['p'], ['q'])])

    def test_weave20(self):
        w = Weave()
        w.add_revision(1, ['a', 'b'], [])
        w.add_revision(2, ['a', 'f', 'y', 'y', 'f', 'b'], [1])
        w.add_revision(3, ['a', 'y', 'b'], [1])
        w.add_revision(4, ['a', 'p', 'z', 'z', 'y', 'z', 'z', 'p', 'b'], [3])
        w.add_revision(5, ['a', 'q', 'z', 'z', 'y', 'z', 'z', 'q', 'b'], [3])
        self.assertEquals(w.merge(4, 5), ['a', (['p'], ['q']), 'z', 'z', 'y', 'z', 'z', (['p'], ['q']), 'b'])

    def test_weave21(self):
        w = Weave()
        w.add_revision(1, ['a', 'b'], [])
        w.add_revision(2, ['a', 'f', 'y', 'y', 'f', 'b'], [1])
        w.add_revision(3, ['a', 'y', 'b'], [1])
        w.add_revision(4, ['a', 'p', 'z', 'm', 'y', 'm', 'z', 'p', 'b'], [3])
        w.add_revision(5, ['a', 'q', 'z', 'n', 'y', 'n', 'z', 'q', 'b'], [3])
        self.assertEquals(w.merge(4, 5), ['a', (['p'], ['q']), 'z', (['m'], ['n']), 'y', (['m'], ['n']), 'z', (['p'], ['q']), 'b'])

    def test_weave_cherry_pick(self):
        w = Weave()
        w.add_revision(1, ['a', 'b', 'c', 'd', 'e', 'f'], [])
        w.add_revision(2, ['a', 'b', 'c', 'd', 'e', 'g'], [1])
        w.add_revision(3, ['b', 'c', 'c', 'd', 'e', 'f'], [])
        self.assertEquals(w.cherry_pick(2, 3), ['b', 'c', 'c', 'd', 'e', 'g'])
        w.add_revision(4, ['a', 'b', 'c', 'd', 'f'], [])
        self.assertEquals(w.cherry_pick(2, 4), ['a', 'b', 'c', 'd', (['e', 'g'], ['f'])])

    def test_weave_cherry_pick_with_removal(self):
        w = Weave()
        w.add_revision(1, ['a', 'b', 'c', 'd', 'e', 'f'], [])
        w.add_revision(2, ['a', 'b', 'c', 'e', 'f'], [1])
        w.add_revision(3, ['a', 'b', 'd', 'e', 'f'], [1])
        self.assertEquals(w.merge(2, 3), ['a', 'b', (['c'], ['d']), 'e', 'f'])
