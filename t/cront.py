from nagi import db
import log
from nagi.thing import Thing, thing_setup
from nagi.cron import Cron
import unittest

db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn': 3, 'maxconn': 10})
thing_setup()


class CronTest(unittest.TestCase):

    def test_add_and_cancel_job(self):
        cron = Cron()
        cron.add_job('cron_job', 'every 5')
        self.assertEqual(Thing('job').find('cron_job').name, 'cron_job')
        cron.cancel_job('cron_job')
        self.assertEqual(Thing('job').find('cron_job'), None)

if __name__ == '__main__':
    log.setdebug(True)
    unittest.main()