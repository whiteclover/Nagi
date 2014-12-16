import unittest
from nagi import db
import time
import log


class TestConnection(unittest.TestCase):

    def setUp(self):
        self.con = db.Connection()

    def test_cursor(self):
        c = self.con.get_cursor()
        c.execute('select 1')
        res = c.fetchone()[0]
        self.assertEqual(1L, res)


class TestDB(unittest.TestCase):

    def setUp(self):
        db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn': 3, 'maxconn': 10})
        db.execute('DROP TABLE IF EXISTS `users`')
        res = db.execute("""CREATE TABLE `users` (
  				`uid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  				`name` varchar(20) NOT NULL,
  				PRIMARY KEY (`uid`))""")
        rows = []
        for _ in range(1, 100):
            rows.append('(%d , "name_%d")' % (_,  _))
        db.execute('INSERT INTO users VALUES ' + ', '.join(rows))

    def tearDown(self):
        db.execute('DELETE FROM users')

    def test_query_one(self):
        res = db.query_one('select count(1) from  users')[0]
        self.assertEqual(99L, res)

    def test_excute(self):
        res = db.execute('insert into users values(%s, %s)', [(100L, 'thomas'), (101L, 'animer')])
        res = db.query('SELECT count(*) FROM users WHERE uid>=100')
        self.assertEqual(2, res[0][0])

    def test_pool(self):
        import threading

        def q(n):
            for i in range(10):
                res = db.query('select count(*) from  users')
                self.assertEqual(99, res[0][0])
        n = 50
        ts = []
        for i in range(n):
            t = threading.Thread(target=q, args=(i,))
            ts.append(t)
        for t in ts:
            t.start()
        for t in ts:
            t.join()

    def test_query(self):
        res = db.query('select name from users limit 5')
        self.assertEqual(len(res), 5)
        res = db.query('select name from users limit %s', (100,), many=20)
        rows = []
        for r in res:
            rows.append(r)
        self.assertTrue(100, len(rows))


class TestSlave(unittest.TestCase):

    def setUp(self):
        db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn': 3, 'maxconn': 10}, key='slave')
        db.execute('DROP TABLE IF EXISTS `users`', key='slave')
        res = db.execute("""CREATE TABLE `users` (
                `uid` int(10) unsigned NOT NULL AUTO_INCREMENT,
                `name` varchar(20) NOT NULL,
                PRIMARY KEY (`uid`))""", key='slave')
        rows = []
        for _ in range(1, 10):
            rows.append('(%d , "name_%d")' % (_,  _))
        db.execute('INSERT INTO users VALUES ' + ', '.join(rows), key='slave')

    def tearDown(self):
        db.execute('DELETE FROM users', key='slave')

    def test_query_one(self):
        res = db.query_one('select count(1) from  users', key='slave')[0]
        self.assertEqual(9L, res)

    def test_excute(self):
        res = db.execute('insert into users values(%s, %s)', [(10L, 'thomas'), (11L, 'animer')], key='slave')
        res = db.query('SELECT count(*) FROM users WHERE uid>=10', key='slave')
        self.assertEqual(2, res[0][0])

    def test_query(self):
        res = db.query('select name from users limit 5', key='slave')
        self.assertEqual(len(res), 5)
        res = db.query('select name from users limit %s', (100,), many=20, key='slave')
        rows = []
        for r in res:
            rows.append(r)
        self.assertTrue(10, len(rows))


if __name__ == '__main__':
    log.setdebug(True)
    unittest.main()
