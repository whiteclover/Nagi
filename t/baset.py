from nagi import db

import log
from nagi.thing.base import BaseEntryThing, EntryThingTrait
from nagi.model import Entry

import unittest

import data

#log.setdebug(True)



class EntryThingTraitTest(unittest.TestCase):

    def setUp(self):
        data.up(lid=2)
        self.e = EntryThingTrait()

    def tearDown(self):
        data.down(lid=2)
        
    def test_find(self):
        e = self.e.find(2, 11)
        self.assertEquals((e.entry_id, e.score, e.rank), (11, 29, None))
        self.assertEqual({'user': 'user_11'}, e.data)

        # not exists
        self.assertEqual(self.e.find(2, 10000), None)
        self.assertEqual(self.e.find(301, 10000), None)

    def test_find_by_score(self):
        es = self.e.find_by_score(2, 29)
        self.assertEqual(len(es), 3)
        es = self.e.find_by_score(2, 33)
        self.assertEqual(len(es), 1)
        e = es[0]
        self.assertEquals((e.entry_id, e.score, e.rank), (1, 33, None))

    def test_find_by_entry_ids(self):
        es = self.e.find_by_entry_ids(2, [11, 13])
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (11, 29, None))
        self.assertEquals((es[1].entry_id, es[1].score, es[1].rank), (13, 29, None))

    def test_save(self):
        # on dup and update
        entry = Entry(1, 2, 34)
        self.e.save(entry)
        e = self.e.find(2, 1)
        self.assertEqual(entry.score, e.score)

        # insert a new entry
        new_entry = Entry(101, 2, 34)
        self.e.save(new_entry)
        e = self.e.find(2, 101)
        self.assertEquals((e.entry_id, e.score), (new_entry.entry_id, e.score))

    def test_delete(self):
        self.e.delete(2, 1)
        entry = self.e.find(2, 1)
        self.assertEqual(entry, None)

    def test_total(self):
        total = self.e.total(2)
        self.assertEqual(100, total)


class BaseEntryThingTest(unittest.TestCase):

    def setUp(self):
        data.up(lid=2)
        self.e = BaseEntryThing()

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

    def test__build_rank_sql(self):
        sql = self.e._build_rank_sql()
        self.assertEqual(sql, 'SELECT  eo.*,\n        (\n        SELECT  COUNT(DISTINCT ei.score)  + 1\n        FROM    entries ei\n        WHERE  eo.lid=ei.lid AND ei.score > eo.score\n        ) AS rank\nFROM   entries eo')
        sql = self.e._build_rank_sql(True)
        self.assertEqual(sql, 'SELECT  eo.*,\n        (\n        SELECT  COUNT(ei.score) \n        FROM    entries ei\n        WHERE  eo.lid=ei.lid AND (ei.score, eo.eid) >= (eo.score, ei.eid)\n        ) AS rank\nFROM   entries eo')

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

        es = self.e.rank(2, 10, 0, True)
        self.assertEqual(len(es), 10)
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (1, 33, 1))
        self.assertEquals((es[1].entry_id, es[1].score, es[1].rank), (2, 32, 2))
        self.assertEquals((es[7].entry_id, es[7].score, es[7].rank), (8, 30, 8))

        es = self.e.rank(2, 10, 1, True)
        self.assertEqual(len(es), 10)
        self.assertEquals((es[0].entry_id, es[0].score, es[0].rank), (2, 32, 2))
        self.assertEquals((es[6].entry_id, es[6].score, es[6].rank), (8, 30, 8))

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