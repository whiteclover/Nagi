from nagi.thing import Thing, EntryThing

class Leaderboard(object):

    def __init__(self, leaderboard):
        leaderboard.bind_entrything(EntryThing(leaderboard.adapter))
        self.leaderboard = leaderboard
        self.entrything = leaderboard.entrything

    @property
    def leaderboard_id(self):
        return self.leaderboard.leaderboard_id

    @property
    def name(self):
        return self.leaderboard.name

    def as_json(self):
        return self.leaderboard.as_json()

    def rank_for_users(self, entry_ids, dense=False):
        return self.entrything.rank_for_users(self.leaderboard_id, entry_ids, dense)

    def rank_for_user(self, entry_id, dense=False):
        return self.entrything.rank_for_user(self.leaderboard_id, entry_id, dense)

    def rank_at(self, rank, dense=False):
        return self.entrything.rank_at(self.leaderboard_id, rank, dense)

    def rank(self, limit=100, offset=0, dense=False):
        return self.entrything.rank(self.leaderboard_id, limit, offset, dense)

    def around_me(self, entry_id, bound=2, dense=False):
        return self.entrything.around_me(self.leaderboard_id, entrything, bound, dense)

    @property
    def total(self):
        return self.entrything.entrything.total(self.leaderboard_id)


def leaderboard(leaderboard_id=None, name=None):
    """Returns Leaderboard if find """
    if leaderboard_id:
        lb = Thing('leaderboard').find(leaderboard_id)
    elif name:
        lb = Thing('leaderboard').find_by_name(name)
    if lb:
        return Leaderboard(lb)