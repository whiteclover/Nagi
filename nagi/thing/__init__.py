_things = dict()
_entrythings  = dict()

def Thing(key):
	return _things.get(key)


def EntryThing(key):
    return _entrythings.get(key)


def thing_setup():
    from nagi.thing.job import JobThing
    from nagi.thing.base import LeaderboardThing, EntryThingTrait, BaseEntryThing
    from nagi.thing.bucket import BucketEntryThing
    from nagi.thing.block import BlockEntryThing
    from nagi.thing.chunk import ChunkEntryThing
    _things['job'] = JobThing()
    _things['leaderboard'] = LeaderboardThing()
    _things['entry'] = EntryThingTrait()
    
    _entrythings['base'] = BaseEntryThing()
    _entrythings['bucket'] = BucketEntryThing()
    _entrythings['block'] = BlockEntryThing()
    _entrythings['chunk'] = ChunkEntryThing()
