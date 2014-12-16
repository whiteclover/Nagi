#!/usr/bin/env python
# Copyright (C) 2014 Thomas Huang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


""" ``nagi.db`` is a simple mysql dabtabase module, current it supports the featues as below::

    # set multiple dabtabases
    # a thread safe connection pool

"""
import MySQLdb
import MySQLdb.cursors
import time
import logging


LOGGER = logging.getLogger('nagi.db')

#  Add the test table in mysql test dabtabase
# DROP TABLE IF EXISTS `users` ;
# CREATE TABLE `users` (
#   `uid` int(10) unsigned NOT NULL AUTO_INCREMENT,
#   `name` varchar(20) NOT NULL,
#   PRIMARY KEY (`uid`)
# )


__connections = {}


def setup(host, user, password, db, max_idle=10, pool_opt=None, port=3306, key='default'):
    db_options = dict(
        host=host,
        user=user,
        passwd=password,
        db=db,
        port=port
    )

    if pool_opt:
        __connections[key] = ThreadSafeConnectionPool(pool_opt.get('minconn', 5),
                            pool_opt.get('maxconn', 10),
                            max_idle, db_options)
    else:
        LOGGER.info('setup adpater to Connection')
        __connections[key] = Connection(max_idle, db_options)


class DBError(Exception):
    pass


class DBPoolError(DBError):
    pass


def query_one(sql, args=None, key='default'):
    """ fecth only one row

    >>> setup('localhost', 'root', '123456', 'test')
    >>> query_one('select 1')[0]
    1L
    """
    try:
        return query(sql, args, key=key)[0]
    except IndexError:
        return None


def query(sql, args=None, many=None, key='default'):
    """The connection raw sql query,  when select table,  show table
        to fetch records, it is compatible the dbi execute method::

    args:
    sql string: the sql stamtement like 'select * from %s'
    args maybe list: Wen set None, will use dbi execute(sql), else
        dbi execute(sql, args), the args keep the original rules, it shuld be tuple or list of list
    many maybe int: whe set, the query method will return genarate an iterate
    key: a key for your dabtabase you wanna use
    """
    con = None
    c = None

    def _all():
        try:
            result = c.fetchmany(many)
            while result:
                for row in result:
                    yield row
                result = c.fetchmany(many)
        finally:
            c and c.close()
            con and __connections[key].putcon(con)

    try:
        con = __connections[key].getcon()
        c = con.get_cursor()
        LOGGER.debug("sql: " + sql + " args:" + str(args))
        c.execute(sql, args)
        if many and many > 0:
            return _all()
        else:
            return c.fetchall()

    except MySQLdb.Error, e:
        LOGGER.error("Error Qeury on %s", e.args[1])
        raise DBError(e.args[0], e.args[1])
    finally:

        many or (c and c.close())
        many or (con and __connections[key].putcon(con))


def execute(sql, args=None, key='default'):
    """It is used for update, delete records::

    >>> setup('localhost', 'root', '123456', 'test')
    >>> execute('insert into users values(%s, %s)', [(1L, 'thomas'), (2L, 'animer')])
    2L
    >>> execute('delete from users')
    True

    """
    con = None
    c = None
    try:
        con = __connections[key].getcon()
        c = con.get_cursor()
        LOGGER.debug("execute sql: " + sql + " args:" + str(args))
        if type(args) is tuple:
            c.execute(sql, args)
        elif type(args) is list:
            if len(args) > 1 and type(args[0]) in (list, tuple):
                c.executemany(sql, args)
            else:
                c.execute(sql, args)
        elif args is None:
            c.execute(sql)
        if sql.lstrip()[:6].upper() == 'INSERT':
            return c.lastrowid
        return c.rowcount
    except MySQLdb.Error, e:
        LOGGER.error("Error Execute on %s", e.args[1])
        raise DBError(e.args[0], e.args[1])

    finally:
        c and c.close()
        con and __connections[key].putcon(con)


class Connection(object):
    """ The Base MySQL Connection:
    >>> con = Connection()
    >>> c = con.get_cursor()
    >>> c.execute('select 1')
    1L
    >>> c.fetchone()[0]
    1L
    """

    def __init__(self, max_idle=10, db_options={}):
        self._db_options = self.default_options()
        self._db_options.update(db_options)
        self._last_used = time.time()
        self._max_idel = max_idle
        self._connect = None

    def default_options(self):
        return {
            'port': 3306,
            'host': 'localhost',
            'user': 'test',
            'passwd': 'test',
            'db': 'test',
            'use_unicode': True,
            'charset': 'utf8'
        }

    def connect(self):
        try:
            self._close()
            self._connect = MySQLdb.connect(**self._db_options)
            self._connect.autocommit(True)
        except MySQLdb.Error, e:
            logging.error("Error MySQL on %s", e.args[1])

    def _close(self):

        if self._connect is not None:
            self._connect.close()
            self._connect = None
    close = _close

    def ensure_connect(self):
        if not self._connect or self._max_idel < (time.time() - self._last_used):
            self.connect()
        self._last_used = time.time()

    def getcon(self):
        return self

    def putcon(self, c):
        pass

    def get_cursor(self, ctype=MySQLdb.cursors.Cursor):
        self.ensure_connect()
        return self._connect.cursor(ctype)


class BaseConnectionPool(object):

    def __init__(self, minconn, maxconn, max_idle=5, db_options={}):
        self.db_options = db_options
        self.max_idle = maxconn
        self.maxconn = maxconn
        self.minconn = minconn if self.maxconn > minconn else int(self.maxconn * 0.2)

    def new_connect(self):
        return Connection(self.max_idle, self.db_options)

    def putcon(self, con):
        pass

    def getcon(self):
        pass

    def close_all(self):
        pass

import threading

class ThreadSafeConnectionPool(BaseConnectionPool):

    def __init__(self, minconn=3, maxconn=10, max_idle=5, db_options={}):
        self._created_conns = 0
        BaseConnectionPool.__init__(self, minconn, maxconn, max_idle, db_options)

        self._lock = threading.RLock()

        self._available_conns = []
        self._in_use_conns = []
        for i in range(self.minconn):
            self._available_conns.append(self.new_connect())

    def getcon(self):
        con = None
        first_tried = time.time()
        while True:
            self._lock.acquire()
            try:
                con = self._available_conns.pop(0)
                self._in_use_conns.append(con)
                break
            except:

                if self._created_conns < self.maxconn:

                    self._created_conns += 1
                    con = self.new_connect()
                    self._in_use_conns.append(con)
                    break
            finally:
                self._lock.release()

            if not con and 3 <= (time.time() - first_tried):
                raise DBPoolError("tried 3 seconds, can't load connection, maybe too many threads")

        return con

    def putcon(self, con):
        self._lock.acquire()
        if con in self._in_use_conns:
            self._in_use_conns.remove(con)
            self._available_conns.append(con)
        self._lock.release()

    def close_all(self):
        with self._lock:
            for conn in self._available_conns:
                conn.close()
            for conn in self._in_use_conns:
                conn.close()
            self._available_conns = []
            self._in_use_conns = []
            self._created_conns = 0


if __name__ == '__main__':
    import doctest
    doctest.testmod()