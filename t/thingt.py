from nagi import db

import log
from nagi.thing.job import JobThing
from nagi.thing.base import LeaderboardThing
from nagi.model import Job, Leaderboard
from datetime import datetime

import unittest


#log.setdebug(True)
db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn': 3, 'maxconn': 10})

class JobThingTest(unittest.TestCase):

    def setUp(self):
        db.execute("DELETE FROM cron WHERE name like 'job%'")
        db.execute('INSERT INTO cron VALUES (1, NULL, %s, %s, NULL, NULL)', ('job_name1', 'every 10'))
        db.execute('INSERT INTO cron VALUES (2, "job_id", %s, %s, NULL, NULL)', ('job_name2', 'every 10'))
        self.jobthing = JobThing()
        self.job = Job(3,  'job_3', 'job_name3', 'every 5')

    def tearDown(self):
        db.execute("DELETE FROM cron WHERE name like 'job%'")

    def test_find(self):
        job = self.jobthing.find('job_name1')
        self.assertEquals((job.name, job.event), ('job_name1', 'every 10'))

        # not exists
        self.assertEqual(self.jobthing.find('job_3'), None)

    def test_find_by_job_id(self):
        jobs = self.jobthing.find_by_job_id('job_id')
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].job_id, 'job_id')

        jobs = self.jobthing.find_by_job_id(None)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].name, 'job_name1')

    def test_save(self):
        # new
        self.job.cron_id = None
        self.jobthing.save(self.job)
        job = self.jobthing.find(self.job.name)
        self.assertEqual(job.name, self.job.name)
        self.assertEqual(job.last_run, None)

        # on dup save
        self.job.cron_id = job.cron_id
        self.job.last_run = datetime.now()
        self.jobthing.save(self.job)
        job = self.jobthing.find(self.job.name)
        self.assertEqual(job.name, self.job.name)
        self.assertTrue(job.last_run)


    def test_delete(self):
        self.job.cron_id = 1
        res = self.jobthing.delete(self.job)
        self.assertTrue(res)

        self.job.cron_id = 4
        res = self.jobthing.delete(self.job)
        self.assertFalse(res)


class LeaderboardThingTest(unittest.TestCase):

    def setUp(self):
        db.execute("DELETE FROM leaderboards WHERE name like 'lb%'")
        db.execute('INSERT INTO leaderboards VALUES (101, %s, %s )', ('lb101', 'base'))
        db.execute('INSERT INTO leaderboards VALUES (102, %s, %s)', ('lb102', 'bucket'))
        self.lbthing = LeaderboardThing()
        self.lb= Leaderboard(103, 'lb103', 'bucket')

    def tearDown(self):
        db.execute("DELETE FROM leaderboards WHERE name like 'lb%'")

    def test_find(self):
        lb = self.lbthing.find(101)
        self.assertEquals((lb.name, lb.adapter), ('lb101', 'base'))

        # not exists
        self.assertEqual(self.lbthing.find(103), None)

    def test_find_by_name(self):
        lb = self.lbthing.find_by_name('lb101')
        self.assertEquals((lb.name, lb.adapter), ('lb101', 'base'))

        # not exists
        self.assertEqual(self.lbthing.find(self.lb.name), None)

    def test_save(self):
        # on dup save
        self.lbthing.save(self.lb)
        lb = self.lbthing.find_by_name(self.lb.name)
        self.assertEquals((lb.name, lb.leaderboard_id), (self.lb.name, self.lb.leaderboard_id))

        # new
        self.lb.leaderboard_id = None
        self.lb.name = 'lb_new'
        self.lbthing.save(self.lb)
        lb = self.lbthing.find_by_name(self.lb.name)
        self.assertEqual(lb.name, self.lb.name)

    def test_delete(self):

        self.lb.leaderboard_id = 101
        res = self.lbthing.delete(self.lb)
        self.assertEqual(self.lbthing.find(101), None)


if __name__ == '__main__':
    unittest.main()

