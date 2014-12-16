import log
from nagi.thing.chunk import ChunkEntryThing
from nagi.model import Entry

import unittest

import data

#log.setdebug(True)


class ChunkEntryThingTest(unittest.TestCase):

    def setUp(self):
        data.up(lid=2)
        self.e = ChunkEntryThing()
        self.e.sort(2)

    def tearDown(self):
        data.down(lid=2)

    def test_rank_for_user(self):
        e = self.e.rank_for_user(2, 11)
        self.assertEquals((e.entry_id, e.score, e.rank), (11, 29, 5))
        e = self.e.rank_for_user(2, 13)
        self.assertEquals((e.entry_id, e.score, e.rank), (13, 29, 5))
        e = self.e.rank_for_user(2, 13, True)
        self.assertEquals((e.entry_id, e.score, e.rank), (13, 29, 13))
        
    def test_rank_for_users(self):
        es = self.e.rank_for_users(2, [11, 13])
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (11, 29, 5))
        self.assertEquals((es[1].entry_id, es[1].score, es[1].rank), (13, 29, 5))

        es = self.e.rank_for_users(2, [11, 13], True)
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (11, 29, 11))
        self.assertEquals((es[1].entry_id, es[1].score, es[1].rank), (13, 29, 13))

    def test_rank_at(self):
        e = self.e.rank_at(2, 11, dense=True)
        self.assertEqual(len(e), 1)
        self.assertEquals((e[0].entry_id, e[0].score, e[0].rank), (11, 29, 11))

        es = self.e.rank_at(2, 2)
        self.assertEqual(len(es), 3)
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (2, 32, 2))
        self.assertEquals((es[1].entry_id, es[1].score, es[1].rank), (3, 32, 2))
        self.assertEquals((es[2].entry_id, es[2].score, es[2].rank), (4, 32, 2))
        
    def test_rank(self):
        es = self.e.rank(2, 3, 4)
        self.assertEqual(len(es), 3)
        e = es[0]
        self.assertEquals((e.entry_id, e.score, e.rank), (5, 31, 3))

        es = self.e.rank(2, 10)
        self.assertEqual(len(es), 10)
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (1, 33, 1))
        self.assertEquals((es[1].score, es[1].rank), (32, 2))
        self.assertEquals((es[2].score, es[2].rank), (32, 2))

    def test_around_me(self):
        es = self.e.around_me(2, 1)
        self.assertEqual(len(es), 3)
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (1, 33, 1))
        self.assertEquals((es[1].entry_id, es[1].score, es[1].rank), (2, 32, 2))
        self.assertEquals((es[2].entry_id, es[2].score, es[2].rank), (3, 32, 2))

        es = self.e.around_me(2, 1, dense=True)
        self.assertEqual(len(es), 3)
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (1, 33, 1))
        self.assertEquals((es[1].entry_id, es[1].score, es[1].rank), (2, 32, 2))
        self.assertEquals((es[2].entry_id, es[2].score, es[2].rank), (3, 32, 3))

        es = self.e.around_me(2, 10)
        self.assertEqual(len(es), 5)
        
if __name__ == '__main__':
    unittest.main()