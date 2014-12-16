from nagi.model.job import Job

from datetime import datetime

__all__ = ['Leaderboard', 'Entry', 'Job']


class Entry(object):

    def __init__(self, eid, lid, score, data=None, created=None, rank=None):
        self.leaderboard_id = lid
        self.entry_id = eid
        self.score = score
        self.data  = data 
        self.created = created or datetime.now()
        self.rank = rank

    def __str__(self):
        return '<Entry leaderboard_id:%d, entry_id:%s, score:%s, data:%s, created:%s, rank:%s>' % (self.leaderboard_id, self.entry_id, self.score, self.data, self.created, self.rank)
    __repr__ = __str__

    def as_json(self):
        based = dict(entry_id=self.entry_id,score=self.score, rank=self.rank, created=self.created)
        if self.data:
            data = self.data.copy()
            data.update(based)
            return data
        return based


class Leaderboard(object):

    def __init__(self, leaderboard_id, name, adapter='base'):
        self.leaderboard_id = leaderboard_id
        self.name = name
        self.adapter = adapter

    def __str__(self):
        return '<Leaderboard leaderboard_id:%d, name:%s, adapter:%s>' % (self.leaderboard_id, self.name, self.adapter)
    __repr__ = __str__

    def bind_entrything(self, entrything):
        self.entrything = entrything

    def as_json(self):
        return {
            'leaderboard_id': self.leaderboard_id,
            'name': self.name,
            'adapter': self.adapter
        }
