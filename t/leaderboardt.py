from nagi import db

import log
from nagi.thing import thing_setup
from nagi.leaderboard import leaderboard


import unittest
import data

db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn': 3, 'maxconn': 10})
thing_setup()


class LeaderboardTest(unittest.TestCase):


    def setUp(self):
        data.up(lid=2)

    def tearDown(self):
        data.down(lid=2)

    def test_leaderboard(self):
        lb = leaderboard(2)
        self.assertTrue(lb)
        lb = leaderboard(name='unittest')
        self.assertTrue(lb)
        lb = leaderboard(name='not_found')
        self.assertFalse(lb)



if __name__ == '__main__':
    log.setdebug(False)
    unittest.main()
