from nagi.model import Job
from nagi import db

class JobThing(object):

    def find(self, name):
        res = db.query('SELECT * FROM cron WHERE name=%s', (name,))
        if res:
            return self._load(res[0])
            
    def find_by_job_id(self, job_id):
        if job_id is None:
            res = db.query('SELECT * FROM cron WHERE job_id IS NULL')
        else:
            res = db.query('SELECT * FROM cron WHERE job_id=%s', (job_id,))
        return [self._load(data) for data in res]

    def _load(self, data):
        return Job(*data)

    def save(self, job):
        if job.cron_id is None:
            return db.execute('INSERT INTO cron(job_id, name, event, next_run, last_run) VALUES (%s, %s, %s, %s, %s)',
                            (job.job_id, job.name, job.event, job.next_run, job.last_run,))
        return db.execute('INSERT INTO cron VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE cron_id=VALUES(cron_id), job_id=VALUES(job_id), event=VALUES(event), next_run=VALUES(next_run), last_run=VALUES(last_run)',
                (job.cron_id, job.job_id, job.name, job.event, job.next_run, job.last_run,))

    def delete(self, job):
        return db.execute('DELETE FROM cron WHERE cron_id=%s', (job.cron_id,))