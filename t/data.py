from nagi import db

db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn': 3, 'maxconn': 10})

def create_lb(lid=2, name='unittest'):
    r = db.query_one('SELECT lid from leaderboards WHERE lid=%s', (lid,))
    if  r:
        return False
    db.execute('INSERT INTO leaderboards VALUES(%s, %s, "base")', (lid, name,))
    return True

def make_entries(lid=2, total=1000000):
    to = 0
    rows = []
    for uid in range(1, total + 1):
        data = r'{\"user\": \"user_%d\"}' %(uid)
        rows.append('(%d, %d, %d, "%s", "2014-08-17 12:49:01")' % (uid,  lid, (total - uid)/3, data))
        if len(rows) == 1000: 
            db.execute('INSERT INTO entries VALUES ' + ', '.join(rows))
            rows = []
    db.execute('INSERT INTO entries VALUES ' + ', '.join(rows))


def up(lid=2, name='unittest'):
    b = create_lb(lid, name='unittest')
    if b:
        make_entries(lid, total=100)


def down(lid):
    db.execute('DELETE FROM entries WHERE lid=%s', (lid,))
    db.execute('DELETE FROM leaderboards WHERE lid=%s', (lid,))
