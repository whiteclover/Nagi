#!/usr/bin/env python

from nagi.model import Job
from nagi import db
import threading
from datetime import datetime
import logging
import uuid
import time
from nagi.thing import Thing, EntryThing
from sys import exc_info

LOGGER = logging.getLogger('nagi.cron')


class Cron(object):

    def __init__(self, limit=5):
        self.threads = []
        self.limit = limit
        self.master = threading.Thread(target=self.work)
        self.master.setDaemon(True)
        self.ready = False

    def run(self):
        LOGGER.info('Start to run corn')
        self.master.run()

    def work(self):
        self.ready = True
        while self.ready:
            try:
                jobs = self.claim()
                if not jobs: # sleep a while
                    time.sleep(1)
                    continue
                threads = []
                for job in jobs:
                    threads.append(threading.Thread(target=self._work, args=(job,)))
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
            except Exception as e:
                cls, e, tb = exc_info()
                LOGGER.error('Unknow exception: %s', e)

    def _work(self, job):
        LOGGER.info('Woking job: %s', job)
        error = False
        try:
            lb = Thing('leaderboard').find_by_name(job.name)
            if not lb:
                LOGGER.warning('Possiable leaderboard <%s> doesn\'t exists', job.name)
                return
            entrything = EntryThing(lb.adapter)
            if entrything:
                entrything.sort(lb.leaderboard_id)
        except Exception as e:
            cls, e, tb = exc_info()
            LOGGER.error('Leaderboard Cron job failed, unhandle error:%s', e)
            error = True
        self.fresh_job(job, error)

    def fresh_job(self, job, error):
        try:
            if job.event_type == 'at':
                Thing('job').delete(job)
                return 
            job.fresh()
            Thing('job').save(job)
        except Exception as e:
            LOGGER.error('Fresh job failed :%s', job)

    def claim(self):
        self.job_id = self.gen_job_id()
        db.execute('UPDATE cron SET job_id=%s WHERE job_id IS NULL AND next_run <= %s LIMIT %s',
         (self.job_id, datetime.now(), self.limit))
        return Thing('job').find_by_job_id(self.job_id)

    def gen_job_id(self):
        return str(uuid.uuid4())

    def stop(self):
        self.ready = False

    def add_job(self, name, event):
        job = Job(None, None, name, event)
        return Thing('job').save(job)

    def cancel_job(self, name):
        job = Thing('job').find(name)
        if job:
            Thing('job').delete(job)