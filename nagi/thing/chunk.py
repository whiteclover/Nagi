
from nagi.model import Entry, Leaderboard
from nagi import db
from collections import namedtuple
import time
import logging
from nagi.thing.base import EntryThingTrait

LOGGER = logging.getLogger(__name__)


CHUNK_BLOCK = 10000
DEFAULT_SCORE_CHUNK = 100


class ChunkEntryThing(EntryThingTrait):

    def rank_for_user(self, leaderboard_id, entry_id, dense=False):
        entry = self.find(leaderboard_id, entry_id)
        if entry:
            if dense:
                data = db.query_one('SELECT from_dense, to_score FROM chunk_buckets WHERE lid=%s AND from_score<=%s AND %s<=to_score', (leaderboard_id, entry.score, entry.score))
                from_dense, to_score = data
                rank = db.query_one('SELECT COUNT(eid) AS rank FROM entries WHERE lid=%s AND eid<%s AND %s<=score AND score<=%s',
                                   (leaderboard_id, entry.entry_id,  entry.score, to_score))
                entry.rank = from_dense + rank[0]
            else:
                data = db.query_one('SELECT from_rank, to_score FROM chunk_buckets WHERE lid=%s AND from_score<=%s AND %s<=to_score', (leaderboard_id, entry.score, entry.score))
                from_rank, to_score = data
                rank = db.query_one('SELECT COUNT(DISTINCT(score)) AS rank FROM entries WHERE lid=%s AND  %s<score AND score<=%s',
                                   (leaderboard_id, entry.score, to_score))[0]
                entry.rank = from_rank + rank
        return entry

    def rank_for_users(self, leaderboard_id, entry_ids, dense=False):
        return [self.rank_for_user(leaderboard_id, entry_id, dense) for entry_id in entry_ids]

    def rank_at(self, leaderboard_id, rank, dense=False):
        if dense:
            data  = db.query_one('SELECT from_dense, from_score, to_score FROM chunk_buckets WHERE lid=%s AND from_dense<=%s AND %s<=to_dense', 
                (leaderboard_id, rank, rank))
            res = db.query('SELECT * FROM entries WHERE lid=%s AND %s<=score AND score<=%s ORDER BY score DESC, eid ASC LIMIT 1 OFFSET %s',
                (leaderboard_id, data[1], data[2], rank - data[0]))
            entries = [self._load(data) for data in res]
            for entry in entries:
                entry.rank = rank
        else:
            data = db.query_one('SELECT from_rank, from_score, to_score FROM chunk_buckets WHERE lid=%s AND from_rank<=%s AND %s<=to_rank', 
                (leaderboard_id, rank, rank))
            if data:
                score = db.query_one('SELECT score FROM entries WHERE lid=%s AND %s<=score AND score<=%s ORDER BY score DESC LIMIT 1 OFFSET %s',
                (leaderboard_id, data[1], data[2], rank - data[0]))[0]
                entries = self.find_by_score(leaderboard_id, score)
                for entry in entries:
                    entry.rank = rank
        return entries

    def rank(self, leaderboard_id, limit=1000, offset=0, dense=False):
        from_score, to_score, from_rank, to_rank = db.query_one('SELECT from_score, to_score, from_rank, to_rank FROM chunk_buckets WHERE lid=%s AND from_rank<=%s AND %s<=to_rank', (leaderboard_id, offset+1, offset+1))
        if to_rank < limit + offset + 1:
            from_score = db.query_one('SELECT from_score FROM chunk_buckets WHERE lid=%s AND from_rank<=%s AND %s<=to_rank', (leaderboard_id, limit+offset+1, limit+offset+1))[0]
            
        sql = 'SELECT * FROM entries WHERE lid=%s AND %s<=score AND score<=%s '
        if dense:
            sql += 'ORDER BY score DESC, eid ASC'
        else:
            sql += 'GROUP BY score, eid ORDER BY score DESC'
        sql += ' LIMIT %s OFFSET %s'
        
        res = db.query(sql, (leaderboard_id, from_score, to_score, limit, offset - from_rank+1))
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
        
    def sort(self, leaderboard_id, chunk_block=CHUNK_BLOCK):
        res = db.query_one('SELECT max(score) as max_score, min(score) as min_score FROM entries WHERE lid=%s', (leaderboard_id,))
        if not res:
            LOGGER.info('Possibly not found Leaderboard:%d', leaderboard_id)
            return
            
        start_time = time.time()
        max_score, min_score = res
        rank, dense = 1, 1
        buckets = []
        self.clear_buckets(leaderboard_id)
        to_score = max_score
        chunk = DEFAULT_SCORE_CHUNK
        from_score = to_score - chunk
        from_score = max(min_score, from_score)
        while to_score >= min_score:
            while True:
                dense_size = self._get_dense_size(leaderboard_id, from_score, to_score)

                if from_score == 0 or (chunk_block / 2) < dense_size <= chunk_block or chunk == 1:
                    break
                chunk += (chunk / 2) if chunk_block / 2 > dense_size else -(chunk / 2)
                from_score = to_score - chunk

            rank_size = self._get_rank_size(leaderboard_id, from_score,  to_score)
            buckets.append(ChunkBucket(leaderboard_id, from_score, to_score, rank, rank + rank_size - 1, dense, dense + dense_size - 1))
            if len(buckets) == 500:
                self.save_buckets(buckets)
                buckets[:] = []
            to_score = from_score - 1
            from_score = to_score - chunk
            from_score = max(min_score, from_score)
            dense += dense_size
            rank += rank_size

        self.save_buckets(buckets)
        LOGGER.info('Chunk sort Leaderboard:%s takes %f (secs)', leaderboard_id, time.time() - start_time)

    def _get_dense_size(self, leaderboard_id, from_score, to_score):
        return db.query_one('SELECT COUNT(score) size FROM entries WHERE lid=%s AND %s<=score AND score<=%s',
            (leaderboard_id, from_score, to_score))[0]

    def _get_rank_size(self, leaderboard_id, from_score, to_score):
        return db.query_one('SELECT COUNT(DISTINCT(score)) size FROM entries WHERE lid=%s AND %s<=score AND score<=%s',
            (leaderboard_id, from_score, to_score))[0]

    def save_buckets(self, buckets):
        if not buckets:
            return

        sql = 'INSERT INTO chunk_buckets(lid, from_score, to_score, from_rank, to_rank, from_dense, to_dense) VALUES '
        rows = []
        for bucket in buckets:
            rows.append('(%d, %d, %d, %d, %d, %d, %d)' % (bucket.leaderboard_id, bucket.from_score,
               bucket.to_score, bucket.from_rank, bucket.to_rank, bucket.from_dense, bucket.to_dense))
        db.execute(sql + ','.join(rows))

    def clear_buckets(self, leaderboard_id):
        return db.execute('DELETE FROM chunk_buckets WHERE lid=%s', (leaderboard_id,))


ChunkBucket = namedtuple('ChunkBucket', ['leaderboard_id', 'from_score', 'to_score', 'from_rank', 'to_rank', 'from_dense', 'to_dense'])
