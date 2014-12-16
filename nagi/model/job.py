
from datetime import datetime, timedelta
import re
from collections import namedtuple


class _AtPattern(object):

    def validate(self, pattern):
        try:
            dt = datetime.strptime(pattern, "%Y%m%d%H%M")
        except:
            return False
        if dt <= datetime.now() + timedelta(minutes=1):
            return False
        return True

    def gen_next_run(self, pattern):
        return datetime.strptime(pattern, "%Y%m%d%H%M")


class _EveryPattern(object):
    
    INTERGE_RE = re.compile('\d+')

    def validate(self, pattern):
        if self.INTERGE_RE.match(pattern):
            s = int(pattern)
            if s >= 2:
                return True
        return False

    def gen_next_run(self, pattern):
        return datetime.now() + timedelta(minutes=int(pattern))


class _CrontabPattern(object):
    """
    Cron format from man 5 crontab:

      field          allowed values
      -----          --------------
      minute         0-59
      hour           0-23
      day of month   1-31
      month          1-12 
      day of week    0-7 
    """
    NUMBER_RE = re.compile('\d+')
    ITEM_RE = re.compile(r'(\d+-\d+/\d+)|(\d+-\d+)|(\d+)')
    RANGES = ('0-59', '0-23', '1-31', '1-12', '0-7')

    VALIDATE_RE = re.compile(r'^(\d+-\d+/\d+)|(\d+-\d+)|(\d+)$')

    def validate(self, pattern):
        parts = pattern.split()
        if len(parts) == 5:
            return bool(all([self.VALIDATE_RE.match(_) for _ in parts]))
        return False

    def gen_next_run(self, pattern , dt=None):
        """Generate crontab iter"""
        cron_pat = self.parse(pattern)
        n = dt or datetime(*datetime.now().timetuple()[:5]) + timedelta(minutes=1)

        while True:
            if n.month not in cron_pat.month:
                n = n.replace(year=n.year + (n.month + 1) / 12, month=(n.month + 1) % 12, day = 1, hour = 0, minute = 0)
                continue
            if n.day not in cron_pat.dom or n.weekday() not in cron_pat.dow:
                n += timedelta(days=1)
                n = n.replace(hour=0, minute=0)
                continue
            if n.hour not in cron_pat.hour:
                n += timedelta(hours=1)
                n = n.replace(minute=0)
                continue
            if n.minute not in cron_pat.minute:
                n += timedelta(minutes=1)
                continue

            return n

    def parse(self, pattern):
        parts = pattern.split()
        if len(parts) != 5:
            raise TypeError("'CrontabPattern':%s  mismatch" % (pattern))
        parts = [p.replace('*', r) for p, r in zip(parts, self.RANGES)]
        pattern = ' '.join(parts)
        return self.parse_pattern(pattern)

    def parse_pattern(self, pattern):
        """
        Parses a pattern like
        '* * * * *' or '1 0 0 0 0'
        into a set that can be evaluated
        """
        parts = pattern.split()
        sets = [set() for x in range(5)]
        for p, out_set in zip(parts, sets):

            for range_step, range_, number in self.ITEM_RE.findall(p):
                if range_step:
                    b, e, s = self._numbers(range_step)
                    out_set |= set(range(b, e + 1, s))
                if range_:
                    b, e = self._numbers(range_)
                    out_set |= set(range(b, e + 1))
                if number:
                    b, = self._numbers(number)
                    out_set.add(b)

        # Weekdays need special treatment: 0 is an alias for 7,
        # so when 0 is present we add 7 as well:
        if 0 in sets[4]:
            sets[4].add(7)
        return _ParsedSpec(*sets)

    def _numbers(self, s):
        return tuple(int(x) for x in self.NUMBER_RE.findall(s))


_ParsedSpec = namedtuple('_ParsedSpec', 'minute hour dom month dow')


class Job(object):

    GEN_NEXT_RUNS = {
        'at': _AtPattern(),
        'every': _EveryPattern(),
        'cron':  _CrontabPattern()
    }

    def __init__(self, cron_id, job_id, name, event, next_run=None, last_run=None):
        self.cron_id = cron_id
        self.job_id = job_id
        self.name = name
        self.event = event
        self.last_run = last_run
        if not next_run:
            if self.validate_event():
                next_run = self.gen_next_run()
            else:
                raise TypeError('The event "%s" is invalid' %(event))
        self.next_run = next_run

    def validate_event(self):
        pat = self.GEN_NEXT_RUNS.get(self.pattern[0])
        if pat:
            return pat.validate(self.pattern[1])
        return False

    def event():
        doc = "The event property."
        def fget(self):
            return self._event

        def fset(self, event):
            """ at %Y%m%d%H%M
                every $minute(s)
                cron $crontab_pattern"""
            self.pattern = self._pattern(event)
            self._event = event
        return locals()
    event = property(**event())

    def as_json(self):
        return self.__dict__.copy()

    def __str__(self):
        return '<Job name:%s, next_run:%s, last_run:%s, crontab:%s>' % (self.name, self.next_run, self.last_run, self.event)
    __repr__ = __str__

    def _pattern(self, event):
        pattern = re.split(r' +', event, 1)
        if len(pattern) != 2:
            raise TypeError("'event':%s pattern mismatch" % (event))
        if pattern[0] not in self.GEN_NEXT_RUNS:
            raise TypeError("Unknow 'event': %s, the event must be in [at, event, cron]" %(event))
        return pattern

    def fresh(self):
        self.job_id = None
        self.next_run = self.gen_next_run()
        self.last_run = datetime.now()

    def gen_next_run(self):
        return self.GEN_NEXT_RUNS[self.pattern[0]].gen_next_run(self.pattern[1])

    @property
    def event_type(self):
        return self.pattern[0]
