
from nagi.model import Entry, Leaderboard
from nagi import db
from nagi.jsonify import loads, dumps


class EntryThingTrait(object):

    def find(self, leaderboard_id, entry_id):
        data = db.query_one('SELECT eid, lid, score, data, created FROM entries WHERE lid=%s AND eid=%s', (leaderboard_id, entry_id))
        if data:
            return self._load(data)

    def find_by_score(self, leaderboard_id, score):
        results = db.query('SELECT eid, lid, score, data, created FROM entries WHERE lid=%s AND score=%s', (leaderboard_id, score))
        return [self._load(data) for data in results]

    def find_by_entry_ids(self, leaderboard_id, entry_ids):
        sql = 'SELECT eid, lid, score, data, created FROM entries WHERE lid=%%s AND  eid IN (%s)' % (', '.join([str(_) for _ in entry_ids]))
        results = db.query(sql, (leaderboard_id, ))
        return [self._load(data) for data in results]

    def _load(self, data):
        data = list(data)
        if data[3]:
            data[3] = loads(data[3])
        return Entry(*data)

    def save(self, entry):
        if entry.data:
            entry.data = dumps(entry.data)
        return db.execute('INSERT INTO entries (eid, lid, score, data, created) VALUES (%s, %s, %s, %s, %s) \
            ON DUPLICATE KEY UPDATE score=VALUES(score)',
                          (entry.entry_id, entry.leaderboard_id, entry.score, entry.data, entry.created))

    def delete(self, leaderboard_id, entry_id):
        return db.execute('DELETE FROM entries WHERE lid=%s AND eid=%s', (leaderboard_id, entry_id))

    def total(self, leaderboard_id):
        data = db.query_one('SELECT COUNT(1) FROM entries WHERE lid=%s', (leaderboard_id,))
        return data[0]


class BaseEntryThing(EntryThingTrait):

    RANK_SQL = """SELECT  eo.*,
        (
        SELECT  COUNT(%sei.score) %s
        FROM    entries ei
        WHERE  eo.lid=ei.lid AND %s
        ) AS rank
FROM   entries eo"""

    def __init__(self):
        pass

    def rank_for_users(self, leaderboard_id, entry_ids, dense=False):
        """Get the rank for by users"""
        sql = self._build_rank_sql(dense)
        sql += '\nWHERE lid=%s AND eid IN (' + ', '.join([str(_) for _ in entry_ids]) + ')'
        results = db.query(sql, (leaderboard_id,))
        return [self._load(data) for data in results]

    def rank_for_user(self, lid, eid, dense=False):
        sql = self._build_rank_sql(dense)
        sql += '\nWHERE lid=%s AND eid=%s'
        data = db.query_one(sql, (lid, eid))
        if data:
            return self._load(data)

    def _build_rank_sql(self, dense=False):
        sql = self.RANK_SQL % (('', '', '(ei.score, eo.eid) >= (eo.score, ei.eid)') if dense else ('DISTINCT ', ' + 1', 'ei.score > eo.score'))
        return sql

    def rank_at(self, leaderboard_id, rank, dense=False):
        res = self.rank(leaderboard_id, 1, rank - 1, dense)
        if res and not dense:
            res = res.pop()
            entries = self.find_by_score(leaderboard_id, res.score)
            for entry in entries:
                entry.rank = res.rank
            return entries
        return res

    def rank(self, leaderboard_id, limit=1000, offset=0, dense=False):
        sql = 'SELECT * FROM entries WHERE lid=%s '
        if dense:
            sql += 'ORDER BY score DESC, eid ASC'
        else:
            sql += 'GROUP BY score, eid ORDER BY score DESC'

        sql += ' LIMIT %s OFFSET %s'
        res = db.query(sql, (leaderboard_id, limit, offset))
        res = [self._load(data) for data in res]
        if res:
            if not dense:
                entry = self.rank_for_user(leaderboard_id, res[0].entry_id, dense)
                offset = entry.rank
            else:
                offset += 1
            self._rank_entries(res, dense, offset)
        return res

    def _rank_entries(self, entries, dense=False, rank=0):
        prev_entry = entries[0]
        prev_entry.rank = rank
        for e in entries[1:]:
            if dense:
                rank += 1
            elif e.score != prev_entry.score:
                rank += 1
            e.rank = rank
            prev_entry = e

    def around_me(self, leaderboard_id, entry_id, bound=2, dense=False):
        me = ghost = self.rank_for_user(leaderboard_id, entry_id, dense)
        if not dense:
            ghost = self.rank_for_user(leaderboard_id, entry_id, True)
        lower = self.get_lower_around(ghost, bound, dense)
        upper = self.get_upper_around(ghost, bound, dense)
        return upper + [me] + lower

    def get_lower_around(self, entry, bound, dense):
        return self.rank(entry.leaderboard_id, bound, entry.rank, dense)

    def get_upper_around(self, entry, bound, dense):
        offset = max(0, entry.rank - bound - 1)
        bound = min(bound, entry.rank)
        if bound == 1:
            return []
        return self.rank(entry.leaderboard_id, bound, offset, dense)


class LeaderboardThing(object):

    def find(self, leaderboard_id):
        data = db.query_one('SELECT * FROM leaderboards WHERE lid=%s', (leaderboard_id,))
        if data:
            return self._load(data)

    def find_by_name(self, name):
        data = db.query_one('SELECT * FROM leaderboards WHERE name=%s', (name,))
        if data:
            return self._load(data)

    def _load(self, data):
        return Leaderboard(*data)

    def save(self, leaderboard):
        if not leaderboard.leaderboard_id:
            return db.execute('INSERT INTO leaderboards (name, adapter) VALUES(%s, %s)', (leaderboard.name, leaderboard.adapter))
        else:
            return db.execute('INSERT INTO leaderboards VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE name=VALUES(name), adapter=VALUES(adapter)',
                             (leaderboard.leaderboard_id, leaderboard.name, leaderboard.adapter))

    def delete(self, leaderboard):
        db.execute('DELETE FROM entries WHERE lid=%s', (leaderboard.leaderboard_id,))
        db.execute('DELETE FROM leaderboards WHERE lid=%s', (leaderboard.leaderboard_id,))
