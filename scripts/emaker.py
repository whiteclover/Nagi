from nagi import db
from random import randint

db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn':3, 'maxconn':10})



def create_lb(lid, name='test_3'):
	r = db.query_one('SELECT lid from leaderboards WHERE name=%s', (name,))
	if not r:
		db.execute('INSERT INTO leaderboards VALUES(%s, %s, "bucket")', (lid, name,))

def make_entries(lid, total=100000):
	to = 0
	rows = []
	for uid in range(1, total + 1):
		data = r'{\"user\": \"user_%d\"}' %(uid)
		rows.append('(%d, %d, %d, "%s", "2014-08-17 12:49:01")' % (uid, lid, randint(0, 10000), data))
		if len(rows) == 500: 
			db.execute('INSERT INTO entries VALUES ' + ', '.join(rows))
			rows = []
	if rows:
		db.execute('INSERT INTO entries VALUES ' + ', '.join(rows))


if __name__ == '__main__':
	for lid in range(4, 11):
		name = 'name_'  + str(lid)
		print name
		create_lb(lid, name)
		make_entries(lid)