from nagi import db
from nagi.thing import Thing, thing_setup
from nagi.model import Job
from nagi.cron import Cron
from datetime import datetime, timedelta
import time
import logging

def setdebug(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')


if __name__ == '__main__':
    setdebug(False)
    db.setup('localhost', 'test', 'test', 'nagi', pool_opt={'minconn':3, 'maxconn':10})
    thing_setup()
    next_run = datetime.now() - timedelta(minutes=10)
    for cron_id in range(4, 11):
        name = 'name_'  + str(cron_id)
        job = Job(cron_id,None, name, event='every 2', next_run=next_run)
        Thing('job').save(job)
    time.sleep(2)
    try:
        cron = Cron(5)
        cron.run()
    except KeyboardInterrupt:
        exit(1)
