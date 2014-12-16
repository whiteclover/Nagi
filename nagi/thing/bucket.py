
from nagi.model import Entry, Leaderboard
from nagi import db
from collections import namedtuple
import time
import logging
from nagi.thing.base import EntryThingTrait

LOGGER = logging.getLogger(__name__)


CHUNK_BLOCK = 100


class BucketEntryThing(EntryThingTrait):

    def rank_for_user(self, leaderboard_id, entry_id, dense=False):
        entry = self.find(leaderboard_id, entry_id)
        if entry:
            if dense:
                data  = db.query_one('SELECT from_dense FROM score_buckets WHERE lid=%s AND score=%s', (leaderboard_id, entry.score))
                from_rank = data[0] 
                rank = db.query_one('SELECT COUNT(eid) as rank FROM entries WHERE lid=%s AND eid<%s AND score=%s', 
                    (leaderboard_id, entry_id, entry.score))[0]
                entry.rank = from_rank + rank 
            else:
                data = db.query_one('SELECT rank FROM score_buckets WHERE lid=%s AND score=%s', (leaderboard_id, entry.score))
                entry.rank = data[0]      
        return entry

    def rank_for_users(self, leaderboard_id, entry_ids, dense=False):
        return [self.rank_for_user(leaderboard_id, entry_id, dense) for entry_id in entry_ids]

    def rank_at(self, leaderboard_id, rank, dense=False):
        if dense:
            data  = db.query_one('SELECT from_dense, to_dense, score FROM score_buckets WHERE lid=%s AND from_dense <= %s AND %s <= to_dense', 
                (leaderboard_id, rank, rank))
            res = db.query('SELECT * FROM entries WHERE lid=%s AND score=%s ORDER BY score DESC, eid ASC LIMIT 1 OFFSET %s',
                (leaderboard_id, data[2], rank - data[0]))
            entries = [self._load(data) for data in res]
            for entry in entries:
                entry.rank = rank
        else:
            score = None
            data = db.query_one('SELECT score FROM score_buckets WHERE lid=%s AND from_dense <= %s AND %s <= to_dense', 
                (leaderboard_id, rank, rank))
            if data:
                score = data[0]
                entries = self.find_by_score(leaderboard_id, score)
                for entry in entries:
                    entry.rank = rank
        return entries


    def rank(self, leaderboard_id, limit=1000, offset=0, dense=False):
        to_score,from_rank, to_rank = db.query_one('SELECT score, from_dense, to_dense FROM score_buckets WHERE lid=%s AND from_dense<=%s AND %s<=to_dense', (leaderboard_id, offset+1, offset+1))
        if to_rank >=limit + offset + 1:
            from_score = to_score
        else:
            from_score = db.query_one('SELECT score FROM score_buckets WHERE lid=%s AND from_dense<=%s AND %s<=to_dense', (leaderboard_id, limit+offset+1, limit+offset+1))[0]
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
        
        res = db.query_one('SELECT max(score) as max_score, min(score) as min_score \
            FROM entries WHERE lid=%s', (leaderboard_id,))
        if not res:
            LOGGER.info('Possibly not found Leaderboard:%d', leaderboard_id)
            return
        start_time = time.time()
        max_score, min_score = res
        rank, dense = 0, 0
        from_score = max_score
        self.clear_buckets_by_score_range(leaderboard_id, from_score + 1, None)
        while from_score >= min_score:
            buckets, rank, dense = self._get_buckets(leaderboard_id, from_score - chunk_block, from_score, rank, dense)
            self.clear_buckets_by_score_range(leaderboard_id, from_score - chunk_block, from_score)
            self.save_buckets(buckets)
            from_score -= chunk_block
        self.clear_buckets_by_score_range(leaderboard_id, None, min_score -1)
        LOGGER.info('Score Bucket sort Leaderboard:%s takes %f (secs)', leaderboard_id, time.time() - start_time)

    def _get_buckets(self, leaderboard_id, from_score, to_score, rank, dense):
        res = db.query('SELECT score, COUNT(score) size FROM entries WHERE lid=%s AND %s<score AND score<=%s GROUP BY score ORDER BY score DESC',
            (leaderboard_id, from_score, to_score))
        buckets = []
        for data in res:
            buckets.append(ScoreBucket(leaderboard_id, data[0], data[1], dense + 1, dense + data[1], rank + 1))
            dense += data[1]
            rank += 1
        return buckets, rank, dense

    def clear_buckets_by_score_range(self, leaderboard_id, from_score, to_score):
        if to_score is None:
            return db.execute('DELETE FROM score_buckets WHERE lid=%s AND %s<score', (leaderboard_id, from_score))
        if from_score is None:
            return db.execute('DELETE FROM score_buckets WHERE lid=%s AND score<=%s', (leaderboard_id, to_score))
        return db.execute('DELETE FROM score_buckets WHERE lid=%s AND %s<score AND score<=%s', (leaderboard_id, from_score, to_score))

    def clear_buckets(self, leaderboard_id):
        return db.execute('DELETE FROM score_buckets WHERE lid=%s', (leaderboard_id,))

    def save_buckets(self, buckets):
        if not buckets:
            return
        sql = 'INSERT INTO score_buckets(score, size, lid, from_dense, to_dense, rank) VALUES '
        rows = []
        for bucket in buckets:
            rows.append('(%d, %d, %d, %d, %d, %d)' % (bucket.score, bucket.size,
                bucket.leaderboard_id, bucket.from_dense, bucket.to_dense, bucket.rank))
        db.execute(sql + ','.join(rows))


#'from_rank', 'to_rank', 'dense'
ScoreBucket = namedtuple('ScoreBucket', ['leaderboard_id', 'score', 'size', 'from_dense', 'to_dense', 'rank'])
