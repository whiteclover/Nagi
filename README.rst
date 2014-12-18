Nagi
####

Nagi is a Leaderboard system that helps you rank million user data.




Design
======



`The Detail Design (中文|chinese) <https://github.com/thomashuang/Nagi/blob/master/design_cn.rst>`_

Introduction
---------------

In system, supporting two leaderboard ways, one is ranking by score DESC,the same score has the same rank; another is 'dense' that ranks by score DESC, entry id ASC, the same score has diffrent rank order by entry id ASC.

In leaderboard attribute 'adapter', has four values ('base', 'bucket', 'block', 'chunk'), they are four leaderboard algorithms, but the kernel algorithm is bucket sort algorithm.

.. note:: When you don't use base adapter to rank leaderboard, you shuld set cron to fresh the bucket table





Base MySQL SQL 
--------------

When set leaderboard adapter to 'base', the system will use the MySQL SQL, realtime sort the entries.
It suits for small data leaderboard that less 10k data.

Score Bucket 
------------

When set leaderboard adapter to 'bucket',  it will summary user count by score to help rank your leaderboard.

Block Bucket
------------

When set leaderboard adapter to 'block', it will summary user's conunt by a static scoce grap, like score block [0-100], [101-200]...,
it can be used to rank the user score histgram is steady and smooth.

Chunk Bucket
------------

When set leaderboard adapter to 'chunk', unlike block algorithm using a static score grap, but is dynamic score grap that makes sure user's count between a suitable range like (5000, 10000]


How to install
==============

Firstly download or fetch it form github then run the command in shell:

.. code-block:: bash

    cd nagi # the path to the project
    python setup.py install

.. note:: Make sure you had installed MySQLdb before install the module

Compatibility
=============

Built and tested under Python 2.7 (maybe supports Python 2.6)

Development
===========

Fork or download it, then run:

.. code-block:: bash 

    cd nagi # the path to the project
    python setup.py develop


Setup Database
==============

* create database in mysql:
* then run the mysql schema.sql script in the project directoy schema:

.. code-block:: bash

    mysql -u yourusername -p yourpassword yourdatabase < schema.sql


if your database has not been created yet, log into your mysql first using:

.. code-block:: bash

    mysql -u yourusername -p yourpassword yourdatabase
    mysql>CREATE DATABASE a_new_database_name
    # = you can =
    mysql> USE a_new_database_name
    mysql> source schema.sql


then:

.. code-block:: bash

    mysql -u yourusername -p yourpassword a_new_database_name < schema.sql


How to use
==========

.. code-block:: python 

    from nagi import db
    from nagi.leaderboard import leaderboard
    from nagi.thing import thing_setup
    
    # setup db setting 
    # pool_opt sets the db pool min connections and max connections
    db.setup('host', 'usern', 'pass', 'database', pool_opt={'minconn': 3, 'maxconn': 10})

    # setup thing_setup, initialize the thing_setup bind the data-mapper
    thing_setup() 
    
    # use the leaderboard api
    lb = leaderboard(leaderboard_id=1) # find leaderboard by leaderboard_id
    lb = leaderboard(name='name')  # load leaderboard by name
    lb.rank_for_user(12) # rank a user by user id
    lb.rank_for_users([12, 2]) # rank users by users

Ranking in the leaderboard
==========================

Ranking by limit and offset
---------------------------

.. code-block:: python

    lb.rank(limit=2, offset=10)
    #=>[<Entry leaderboard_id:2, entry_id:11, score:29, data:{u'user': u'user_11'}, created:2014-08-17 12:49:01, ra
    leaderboard_id:2, entry_id:12, score:29, data:{u'user': u'user_12'}, created:2014-08-17 12:49:01, rank:5]

When set the dense:

.. code-block:: python

    lb.rank(limit=2, offset=10, dense=True)
    #=> [<Entry leaderboard_id:2, entry_id:11, score:29, data:{u'user': u'user_11'}, created:2014-08-17 12:49:01, rank:11>, <Entr
    # y leaderboard_id:2, entry_id:12, score:29, data:{u'user': u'user_12'}, created:2014-08-17 12:49:01, rank:12>]


Ranking for user(s)
-----------------

.. code-block:: python

    lb.rank_for_user(11)
    #=> <Entry leaderboard_id:2, entry_id:11, score:29, data:{u'user': u'user_11'}, created:2014-08-17 12:49:01, rank:5>

    lb.rank_for_user(11, True) # dense rank
    #=><Entry leaderboard_id:2, entry_id:11, score:29, data:{u'user': u'user_11'}, created:2014-08-17 12:49:01, rank:11>

    lb.rank_for_users([1,11])
    #=> [<Entry leaderboard_id:2, entry_id:1, score:33, data:{u'user': u'user_1'}, created:2014-08-17 12:49:01, rank:1>, <Entry
    # leaderboard_id:2, entry_id:11, score:29, data:{u'user': u'user_11'}, created:2014-08-17 12:49:01, rank:5>]

    lb.rank_for_users([1,11], True) # dense rank
    #=> [<Entry leaderboard_id:2, entry_id:1, score:33, data:{u'user': u'user_1'}, created:2014-08-17 12:49:01, rank:1>, <Entry
    #leaderboard_id:2, entry_id:11, score:29, data:{u'user': u'user_11'}, created:2014-08-17 12:49:01, rank:11>]

Rank at position
---------------

.. code-block:: python

    lb.rank_at(3)
    #=> [<Entry leaderboard_id:2, entry_id:2, score:32, data:{u'user': u'user_2'}, created:2014-08-17 12:49:01, rank:2>, <Entry
    # leaderboard_id:2, entry_id:3, score:32, data:{u'user': u'user_3'}, created:2014-08-17 12:49:01, rank:2>, <Entry leaderbo
    # ard_id:2, entry_id:4, score:32, data:{u'user': u'user_4'}, created:2014-08-17 12:49:01, rank:2>]

    lb.rank_at(3, True) # dense rank
    #=> [<Entry leaderboard_id:2, entry_id:3, score:32, data:{u'user': u'user_3'}, created:2014-08-17 12:49:01, rank:3>]

Around me
---------

Retrieve ranks around a user:

.. code-block:: python

    lb.around_me(33)
    #=> [<Entry leaderboard_id:2, entry_id:31, score:23, data:{u'user': u'user_31'}, created:2014-08-17 12:49:01, rank:11>, <Ent
    # ry leaderboard_id:2, entry_id:32, score:22, data:{u'user': u'user_32'}, created:2014-08-17 12:49:01, rank:12>, <Entry le
    # aderboard_id:2, entry_id:33, score:22, data:{u'user': u'user_33'}, created:2014-08-17 12:49:01, rank:12>, <Entry leaderb
    # oard_id:2, entry_id:34, score:22, data:{u'user': u'user_34'}, created:2014-08-17 12:49:01, rank:12>, <Entry leaderboard_
    # id:2, entry_id:35, score:21, data:{u'user': u'user_35'}, created:2014-08-17 12:49:01, rank:13>]

    lb.around_me(33, dense=True)
    #=> [<Entry leaderboard_id:2, entry_id:31, score:23, data:{u'user': u'user_31'}, created:2014-08-17 12:49:01, rank:31>, <Ent
    # ry leaderboard_id:2, entry_id:32, score:22, data:{u'user': u'user_32'}, created:2014-08-17 12:49:01, rank:32>, <Entry le
    # aderboard_id:2, entry_id:33, score:22, data:{u'user': u'user_33'}, created:2014-08-17 12:49:01, rank:33>, <Entry leaderb
    # oard_id:2, entry_id:34, score:22, data:{u'user': u'user_34'}, created:2014-08-17 12:49:01, rank:34>, <Entry leaderboard_
    # id:2, entry_id:35, score:21, data:{u'user': u'user_35'}, created:2014-08-17 12:49:01, rank:35>]

    lb.around_me(33, bound=1)
    #=> [<Entry leaderboard_id:2, entry_id:33, score:22, data:{u'user': u'user_33'}, created:2014-08-17 12:49:01, rank:12>, <Ent
    # ry leaderboard_id:2, entry_id:34, score:22, data:{u'user': u'user_34'}, created:2014-08-17 12:49:01, rank:12>]


Set Cron to fresh the leaderbaord
=================================

The cron is a distributed scheduler that freshs leaderboard:

.. code-block:: python

    # you shuoud setup database firstly, see setup database section
    from nagi.cron import Cron
    cron = Cron(limit=5) # set the threads count to work 
    cron.add_job('cron_job', 'every 5')
    cron.cancel_job('cron_job')
    cron.run() # start the scheduler

Add job to cron
---------------

You just need to add a job once time, it will stroe in database for reuse, name is the name of leaderboard need fresh:

.. code-block:: python

    cron.add_job(name='cron_job', event='every 5')
    cron.add_job(name='cron_job', event='at 201408310804')

Cancel a job
-------------

Delete a job from database by job name:

.. code-block:: python

    cron.cancel_job('cron_job')

Event
------

When you add job to scheduler, you see a event arugement. it is a specfic how to fresh leaderboard. Current event supports three types:

at
~~~

this event will only run once, in a future datetime, it should at least 1 minute speed from now: the pattern as below::

    at %Y%m%d%H%M

every
~~~~~

this event will run in loop by minute(s), the pattern is a  unsiged integer::

    every minute(s)

cron
~~~~

this event pattern is pattern of crontab, current supports::

      field          allowed values
      -----          --------------
      minute         0-59
      hour           0-23
      day of month   1-31
      month          1-12 
      day of week    0-7 

and the every sub pattern only support below regex expression format::

    ^(\d+-\d+/\d+)|(\d+-\d+)|(\d+)$

API
===

Model
-----

Leaderboard
~~~~~~~~~~~

Leaderboard has three attributes:

    :name: an unique name for human beings
    :leaderboard_id: an  identifier generate by mysql
    :adapter: the name of leaboarderd adapter, see the Desgin session

Entry
~~~~~

    :leaderboard_id: the leaboarderd id means what leaderboard the current entry beings
    :entry_id:  An unique identifier in one leaderboard, you can set user id as entry id
    :score: the user's score
    :data:  a custom json data, like '{"name": "Natume"}'
    :created: the entry creation datetime
    :rank:  only set in LeaderBoard when rank


Thing
-----

The Project Architecture is data mapper pattern. The most important parts are Thing and Model, Thing (Mapper) is Data Access Layer that performs bidirectional transfer of data between a persistent data store.

Thing is used to store the model to database, current supports "entry", "job", "leadebaord":

.. code-block:: python

    backed = Thing('entry')
    backed.save(Entry(...))


Entry Thing
~~~~~~~~~~~

    :find: load by leaderboard_id and eid
    :find_by_score: find entry by score from leaderboard
    :find_by_entry_ids: find entries by user ids
    :save: save entry to database, if duplicete, will update the entry
    :delete: delete the entry from database
    :total: the leaderboard entries total count

 
Leaderboard Thing
~~~~~~~~~~~~~~~~~

    :find: load leaderboard from database by leaderboard id
    :find_by_name: load job from database by name
    :save: if leaderboard_id is None, create a new in database, else update
    :delete: delele leaderboard from database by Leaderboard(leaderboard_id)



LICENSE
=======

    Copyright (C) 2014 Thomas Huang

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


