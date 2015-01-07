LeaderBoard
###########

排行榜在游戏中非常常见的功能之一，在游戏中有各种排行榜，如工会活跃度，玩家的英雄战斗力排行等。当数据上亿时，如果使用数据库直排是致命的慢，远远超出用户接受的响应时间。也对数据库造成非常大的压力。本文将会讲述千万用户级别的用户排行系统的一些设计理念并讲述数据库直排以及使用桶排和内存数据优化排行榜。

在讲述设计前，有必要先了解一些基础理论，文章将会先讲述什么排行榜的类别，排行规则和排名分布，然后进一步结合以往写的一个简单的排行系统Nagi，讲述数据库直排和使用桶排技术，以及内存缓存技术等。


排行榜的类别
=============

刷新频率
---------

如果以排行榜的刷新频率来分类可分为及时排行榜，和周期排行榜。


及时排行榜
~~~~~~~~~~~

排行榜的排名能及时反映用户的排变名化，但可能是近似的排名。


周期性排行榜
~~~~~~~~~~~~~

排行榜将会在一定周期内刷新排名，如日排行，周排行，月排行等


准确性分类
------------


精准排名
~~~~~~~~~~

能够准确的反应当前玩家的某段时间，或者当前的排名。


近似排名
~~~~~~~~

近似排名能够反映用户的排名变化和接近真实排名也许会稍稍低于真实排名，或者高于真实排名。总之可能与真实的排名有一定差别。



排行规则
==========

排名规则，这里并不是如竞技场，使用交换排名的方式，一个新用户进入竞技场时只要简单的统计下当前竞技场用户数量就可以初始化其排名，随着玩家挑战高名次的玩家，如果胜利就交换名次这类规则。而是诸如工会活跃度可能是当前工会所有工会成员的活跃度总和作为工会活跃度、或工会所有玩家战斗力总和作为工会战斗力。这类因为最后由唯一属性（如工会活跃度，工会战斗力）决定排名的归为简单排名（唯一属性排名）。

你可能会为担忧如何计算工会的战斗力。那么考虑一个简单的游戏功能如签到排名，规则是用户每天签到将会记录用户最近连续签到的天数，如果某天用户忘记签到，那么用户签到天数将会从零开始重新计算，除非用户补签。如果用户签到天数越多，那么用户排名越高这类就是简单的排名，仅有单一属性决定玩家的排名。但是由于这个排名可能因为大多数用户都在游戏开始就持续的签名，这样就会有很多玩家排名一致，但为了保证每个用户都有不同的排名，于是将由用户id来区分排名，id越小排名越靠前，这类排名签到天数结合用户id就有多个属性决定排名就是复合属性排名。


用户排名的分布
===============

在设计排名系统时一定要注意到用户排名的分布，正如上面讲到签到系统，是非常符合‘二八法则’的，大多数用户的排名将会非常接近或者相同。这类分布也可能会相近于正太分布。两端的用户越来越少，中间用户越来多。这样造成大量用户的排名相同。所以如果有可能应该制定比较好的游戏规则，使用户的排行分散均匀。


算法设计
==========


算法设计将结合个人一个项目Nagi来讲述具体设计。 Nagi是一个抽象的排行榜系统，在系统中把所有需要排行的数据抽象成一个具有一个积分的实体对象。并且可以排行多个排行榜，数据库使用的是MySQL。


基础表设计
-----------


用户积分表（实体表）
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sql

    CREATE TABLE entries (
      eid INT(11) unsigned NOT NULL COMMENT 'The unique identifier for a entry in a leaderboards.',
      lid MEDIUMINT(8) unsigned NOT NULL,
      score INT(11) unsigned NOT NULL,
      data VARCHAR(1024) DEFAULT NULL COMMENT 'The custom entry data',
      created DATETIME NOT NULL DEFAULT NOW() COMMENT 'The DATETIME when the entry was created.',

      PRIMARY KEY (lid, eid),
      KEY user_entry (lid, score)
    ) ENGINE=InnoDB CHARSET=utf8;

:eid: 实体唯一标识符（在签到系统相当于用户id）
:score: 排名积分（在签到系统相当于签到天数）
:data: 存放实体的一些自定义数据，json序列化数据
:created: 创建时间
:lid: 排行榜唯一标识，参考leaderboards表


排行榜表
~~~~~~~~~

.. code-block:: sql

    CREATE TABLE leaderboards (
      lid MEDIUMINT(8) unsigned NOT NULL AUTO_INCREMENT,
      name VARCHAR(124) NOT NULL,
      adapter VARCHAR(16),

      PRIMARY KEY (lid),
      UNIQUE KEY name (name)
    ) ENGINE=InnoDB CHARSET=utf8;

:lid: 排行榜唯一标识 
:name: 可读的排行榜名
:adapter: 这个用来决定使用什么什么算法做排行榜

API
~~~~~

这里主要讲述两个api， rank和rank_for_user

rank（limit, offset， dense=False）
--------------------------------------

接口来可以做排行榜分页

rank（1000, 0） 将会获取到排名前1000的用户。


rank_for_user(eid， dense=False)
-------------------------------------

将通过eid（对于签到系统里面是uid）来获取该玩家的排名。

.. note:: 

    接口中的dense为True将会使用签到天数和用户id复合属性排名保证用户排名的唯一性。


使用数据库直排
================


数据库直排，算法比较低效，但数据少量时，依旧是最高效最简单的算法。



rank_for_user
-------------


获取某个用户排名核心sql如下

.. code-block:: python

    RANK_SQL = """SELECT  eo.*,
            (
            SELECT  COUNT(%sei.score) %s
            FROM    entries ei
            WHERE  eo.lid=ei.lid AND %s
            ) AS rank
    FROM   entries eo"""


    def rank_for_user(self, lid, eid, dense=False):
        sql = self._build_rank_sql(dense)
        sql += '\nWHERE lid=%s AND eid=%s'
        data = db.query_one(sql, (lid, eid))
        if data:
            return self._load(data)

    def _build_rank_sql(self, dense=False):
        if dense:
            sql = self.RANK_SQL % (('', '', '(ei.score, eo.eid) >= (eo.score, ei.eid)')  
        else:
            sql = self.RANK_SQL %('DISTINCT ', ' + 1', 'ei.score > eo.score'))
        return sql

核心一条低效的sql统计出当前用户的排名，代码中dense为True是使用复合属性，就是用户排名将不会重复。

rank
-----

随着offset增大，查询效率会越来越低，返回的数据真实性也会降低。

.. code-block:: python

   def rank(self, leaderboard_id, limit=1000, offset=0, dense=False):
        sql = 'SELECT * FROM entries WHERE lid=%s '
        if dense:
            sql += 'ORDER BY score DESC, eid ASC'
        else:
            sql += 'GROUP BY score, eid ORDER BY score DESC'

        sql += ' LIMIT %s OFFSET %s'
        res = db.query(sql, (leaderboard_id, limit, offset))
        res = [self._load(data) for data in res]
        if res:
            if not dense:
                entry = self.rank_for_user(leaderboard_id, res[0].entry_id, dense)
                offset = entry.rank
            else:
                offset += 1
            self._rank_entries(res, dense, offset)
        return res

    def _rank_entries(self, entries, dense=False, rank=0):
        prev_entry = entries[0]
        prev_entry.rank = rank
        for e in entries[1:]:
            if dense:
                rank += 1
            elif e.score != prev_entry.score:
                rank += 1
            e.rank = rank
            prev_entry = e


同样通过低效的order  group选出用户后，然后获取到第一个用户排名，然后简单的在程序中做排名。
 


直排的性能
-----------

对于100万数据，如果使用数据直排，取某个用户平均需要5s，所以这种算法的排名，基本适数据量小于10w数据量的排名。


桶排
====

桶排是使用桶排序结合数据库特性优化的一种排行榜算法，在使用不同数据库实现时，有必要了解数据库的特性，才能设计好的系统。

桶排适合周期性排行，桶排在用户更新积分时会改变影响整个排行，整体来说就是个近似排名。
桶排的优化原则是保证区间桶的用户数量在适合范围，保证用户可接受的响应时间。


积分桶 (计数排序)
---------------------


对于签到系统,签到天数在  [0, 5000] 范围绝对是够用的（有游戏能做到13年一直保持维护更新？）。那么以签到天数作为桶号，桶统计当前签到天数为当前桶号用户数量，于是最多可能有5001桶，每个桶统计当前得分用户的数量。这样可以用简单的sql:

    SELECT SUM(uid) FROM entries GROUP BY score

来获取桶信息，然后计算出各个积分的排名区间比如得当前签到天数为5000且有1000个用户。 如果使用复合uid来排名那么桶号为5000的排名区间为[1-1000] ，如果仅仅使用积分作为排名那么桶5000的排名为1。


因为桶排需要记录额外的桶信息，所以需要额外的表来保存桶信息。


积分桶表如下：

.. code-block:: sql

    CREATE TABLE score_buckets (
      lid MEDIUMINT(8) unsigned NOT NULL,
      score INT(11) unsigned NOT NULL,
      size INT(11) unsigned NOT NULL,
      from_dense INT(11) unsigned NOT NULL,
      to_dense INT(11) unsigned NOT NULL,
      rank INT(11) unsigned NOT NULL,

      PRIMARY KEY leaderboard_score (lid, score),
      KEY dense (from_dense, to_dense)
    ) ENGINE=InnoDB CHARSET=utf8;



:lid: 排行榜唯一标识 
:score: 积分桶当前桶号，也就是积分 
:size: 用于记录当前桶的用户数量
:from_dense: 记录复合属性时桶中用户的最高排名（起始排名）
:to_dense: 记录复合属性时桶中用户的最低排名（终止排名）
:rank: 记录唯一属性时当前桶的排名


桶统计流程
~~~~~~~~~~~~~~~

.. code-block:: python

    def sort(self, leaderboard_id, chunk_block=CHUNK_BLOCK):

        # 获取当前排行榜的最高分与最低分
        res = db.query_one('SELECT max(score) as max_score, min(score) as min_score \
            FROM entries WHERE lid=%s', (leaderboard_id,))

        max_score, min_score = res
        rank, dense = 0, 0
        from_score = max_score
        #清空可能比现在最高分更高的桶
        self.clear_buckets_by_score_range(leaderboard_id, from_score + 1, None)

        # 因为一次统计所有桶过于费时，所以切割分桶，并清空以前的桶数据，写入新的的桶数据
        while from_score >= min_score:
            buckets, rank, dense = self._get_buckets(leaderboard_id, from_score - chunk_block, from_score, rank, dense)
            self.clear_buckets_by_score_range(leaderboard_id, from_score - chunk_block, from_score)
            self.save_buckets(buckets)
            from_score -= chunk_block
        # 清空比当前排行榜最低积分低的桶数据
        self.clear_buckets_by_score_range(leaderboard_id, None, min_score -1)

    def _get_buckets(self, leaderboard_id, from_score, to_score, rank, dense):
        """获取新的桶区间数据"""
        res = db.query('SELECT score, COUNT(score) size FROM entries WHERE lid=%s AND %s<score AND score<=%s GROUP BY score ORDER BY score DESC',
            (leaderboard_id, from_score, to_score))
        buckets = []
        for data in res:
            buckets.append(ScoreBucket(leaderboard_id, data[0], data[1], dense + 1, dense + data[1], rank + 1))
            dense += data[1]
            rank += 1
        return buckets, rank, dense

    def clear_buckets_by_score_range(self, leaderboard_id, from_score, to_score):
        """清空桶区间"""
        if to_score is None:
            return db.execute('DELETE FROM score_buckets WHERE lid=%s AND %s<score', (leaderboard_id, from_score))
        if from_score is None:
            return db.execute('DELETE FROM score_buckets WHERE lid=%s AND score<=%s', (leaderboard_id, to_score))
        return db.execute('DELETE FROM score_buckets WHERE lid=%s AND %s<score AND score<=%s', (leaderboard_id, from_score, to_score))

    def save_buckets(self, buckets):
        """写入桶数据"""
        if not buckets:
            return
        sql = 'INSERT INTO score_buckets(score, size, lid, from_dense, to_dense, rank) VALUES '
        rows = []
        for bucket in buckets:
            rows.append('(%d, %d, %d, %d, %d, %d)' % (bucket.score, bucket.size,
                bucket.leaderboard_id, bucket.from_dense, bucket.to_dense, bucket.rank))
        db.execute(sql + ','.join(rows))


1. 因为不可能一次用使用group by统计出所有桶，因为这样可能太耗费内存和时间，所以先选出最高积分(max)和最低积分(min)：
2. 利用获取的最高和最低积分，使用一个阈值分割桶, 比如阈值为500,那么分割后为[max, max - 500], [max - 501, max - 1000],..[?, min]直到最小积分。
3. 如sort方法中先清空相关区间的桶数据然后查询写入新的桶数据。



rank_for_user
~~~~~~~~~~~~~~~~~

可以轻松根据用户id获取到score后使用如下api能获取到当前用户的排名。

.. code-block:: python

    def rank_for_user(self, leaderboard_id, entry_id, dense=False):
        entry = self.find(leaderboard_id, entry_id)
        if entry:
            if dense:
                data  = db.query_one('SELECT from_dense FROM score_buckets WHERE lid=%s AND score=%s', (leaderboard_id, entry.score))
                from_rank = data[0] 
                rank = db.query_one('SELECT COUNT(eid) as rank FROM entries WHERE lid=%s AND eid<%s AND score=%s', 
                    (leaderboard_id, entry_id, entry.score))[0]
                entry.rank = from_rank + rank 
            else:
                data = db.query_one('SELECT rank FROM score_buckets WHERE lid=%s AND score=%s', (leaderboard_id, entry.score))
                entry.rank = data[0]      
        return entry


rank
~~~~~

使用桶排 rank算法相对复杂些：

.. code-block:: python

    def rank(self, leaderboard_id, limit=1000, offset=0, dense=False):
        to_score,from_rank, to_rank = db.query_one('SELECT score, from_dense, to_dense FROM score_buckets WHERE lid=%s AND from_dense<=%s AND %s<=to_dense', (leaderboard_id, offset+1, offset+1))
        if to_rank >=limit + offset + 1:
            from_score = to_score
        else:
            from_score = db.query_one('SELECT score FROM score_buckets WHERE lid=%s AND from_dense<=%s AND %s<=to_dense', (leaderboard_id, limit+offset+1, limit+offset+1))[0]
        sql = 'SELECT * FROM entries WHERE lid=%s AND %s<=score AND score<=%s '
        if dense:
            sql += 'ORDER BY score DESC, eid ASC'
        else:
            sql += 'GROUP BY score, eid ORDER BY score DESC'
        sql += ' LIMIT %s OFFSET %s'
        
        res = db.query(sql, (leaderboard_id, from_score, to_score, limit, offset - from_rank+1))
        res = [self._load(data) for data in res]
        if res:
            if not dense:
                entry = self.rank_for_user(leaderboard_id, res[0].entry_id, dense)
                offset = entry.rank
            else:
                offset += 1
            self._rank_entries(res, dense, offset)
        return res

    def _rank_entries(self, entries, dense=False, rank=0):
        prev_entry = entries[0]
        prev_entry.rank = rank
        for e in entries[1:]:
            if dense:
                rank += 1
            elif e.score != prev_entry.score:
                rank += 1
            e.rank = rank
            prev_entry = e

代码流程是：

1. 获取到当前排名范围的积分分布范围
2. 通过缩小积分范围从entries获取到根据积分排序好的用户
3. 然后我们只要获取到第一个用户的排名，然后在业务代码中排好其他用户的名次就行。



积分桶的优点与缺点
~~~~~~~~~~~~~~~~~~~~~~

这类排行算法，比较适合实体积分范围比较小。由于二八法则的用户积分分布，都可造成单通用户数量过于膨大。积分范围过广泛如[0, 1000000000) 这样桶的数量过于多。算法也不适宜了。

均匀区间桶
------------

对于工会活跃度积分范围可能在 [0, 1000000000) 积分分布比较分散，如果使用积分桶，需要耗费比较长的计算时间，查询用户排名也会变慢。这时可使用均匀区间桶，
我们把积分分为这样的连续均匀递增区间[0, 10000), [10001, 20000), .... ，然后桶不再只对应一个积分，而是对应相关的积分区间，比如桶1对应[0, 10000),桶2对应[10000, 20000)。这样的桶算法也就是区间桶，其实是最为常见的桶排序。

区间桶存储表
~~~~~~~~~~~~~~~


.. code-block:: sql

    CREATE TABLE block_buckets  (
      lid MEDIUMINT(8) unsigned NOT NULL,
      from_score INT(11) unsigned NOT NULL,
      to_score INT(11) unsigned NOT NULL,
      from_rank INT(11) unsigned NOT NULL,
      to_rank INT(11) unsigned NOT NULL,
      from_dense INT(11) unsigned NOT NULL,
      to_dense INT(11) unsigned NOT NULL,

      PRIMARY KEY leaderboard_score (lid,from_score, to_score)
    ) ENGINE=InnoDB CHARSET=utf8;


:lid: 排行榜唯一标识 
:from_score: 记录区间桶的低端
:to_score: 记录区间桶的高端
:from_rank: 记录当前桶唯一属性排名时的中用户最高排名
:to_rank: 记录当前桶唯一属性排名时的中用户最低排名
:from_dense: 记录复合属性时桶中用户的最高排名（起始排名）
:to_dense: 记录复合属性时桶中用户的最低排名（终止排名）


桶排算法如下：

.. code-block:: python

    def sort(self, leaderboard_id, chunk_block=BUCKET_BLOCK):
        """计算刷新保存桶信息"""

        # 获取当前排行榜的最高分与最低分
        res = db.query_one('SELECT max(score) as max_score, min(score) as min_score FROM entries WHERE lid=%s', (leaderboard_id,))
        if not res: return

        max_score, min_score = res
        if chunk_block is None and max_score > min_score:
            chunk_block = (max_score - min_score) / (self.total(leaderboard_id)/ (max_score - min_score))
        elif max_score == min_score:
            chunk_block = BUCKET_BLOCK

        rank, dense = 1, 1
        buckets = []
        self.clear_buckets(leaderboard_id)
        to_score = max_score
        from_score = to_score - chunk_block
        from_score = max(min_score, from_score)

        # 切割区间保存并保存桶信息
        while to_score >= min_score:
            dense_size = self._get_dense_size(leaderboard_id, from_score, to_score)
            rank_size = self._get_rank_size(leaderboard_id, from_score,  to_score)
            buckets.append(BlockBucket(leaderboard_id, from_score, to_score, rank, rank + rank_size - 1, dense, dense + dense_size - 1))
            if len(buckets) == 500:
                self.save_buckets(buckets)
                buckets = []
            to_score = from_score - 1
            from_score = to_score - chunk_block
            from_score = max(min_score, from_score)
            dense += dense_size
            rank += rank_size

        self.save_buckets(buckets)

    def _get_dense_size(self, leaderboard_id, from_score, to_score):
        """获取当前区间的复合属性时的用户数量"""
        return db.query_one('SELECT COUNT(score) size FROM entries WHERE lid=%s AND %s<=score AND score<=%s',
            (leaderboard_id, from_score, to_score))[0]

    def _get_rank_size(self, leaderboard_id, from_score, to_score):
        """获取当前区间的唯一属性时的用户数量""""""
        return db.query_one('SELECT COUNT(DISTINCT(score)) size FROM entries WHERE lid=%s AND %s<=score AND score<=%s',
            (leaderboard_id, from_score, to_score))[0]

    def save_buckets(self, buckets):
        """保存桶数据"""
        if not buckets: return

        sql = 'INSERT INTO block_buckets(lid, from_score, to_score, from_rank, to_rank, from_dense, to_dense) VALUES '
        rows = []
        for bucket in buckets:
            rows.append('(%d, %d, %d, %d, %d, %d, %d)' % (bucket.leaderboard_id, bucket.from_score,
               bucket.to_score, bucket.from_rank, bucket.to_rank, bucket.from_dense, bucket.to_dense))
        db.execute(sql + ','.join(rows))

    def clear_buckets(self, leaderboard_id):
        """清空排行榜桶数据"""
        return db.execute('DELETE FROM block_buckets WHERE lid=%s', (leaderboard_id,))

    BlockBucket = namedtuple('BlockBucket', ['leaderboard_id', 'from_score',
     'to_score', 'from_rank', 'to_rank', 'from_dense', 'to_dense'])



流程是：

1. 获取当前排行榜的最高和最低积分
2. 利用最高和最低积分，使用一个阈值分割出区间桶, 比如阈值为500,那么分割后为[max, max - 500], [max - 501, max - 1000],..[?, min]直到最小积分。
3. 获取出当前桶的排名范围，保存刷新


rank_for_user
~~~~~~~~~~~~~~~~~

通过entry_id 获取到用户后使用用户的积分获取到积分所在桶，然后利用桶的排名范围和积分范围缩小sql排序的范围，统计出用户的排名

.. code-block:: python

    def rank_for_user(self, leaderboard_id, entry_id, dense=False):
        entry = self.find(leaderboard_id, entry_id)
        if entry:
            if dense:
                data = db.query_one('SELECT from_dense, to_score FROM chunk_buckets WHERE lid=%s AND from_score<=%s AND %s<=to_score', (leaderboard_id, entry.score, entry.score))
                from_dense, to_score = data
                rank = db.query_one('SELECT COUNT(eid) AS rank FROM entries WHERE lid=%s AND eid<%s AND %s<=score AND score<=%s',
                                   (leaderboard_id, entry.entry_id,  entry.score, to_score))
                entry.rank = from_dense + rank[0]
            else:
                data = db.query_one('SELECT from_rank, to_score FROM chunk_buckets WHERE lid=%s AND from_score<=%s AND %s<=to_score', (leaderboard_id, entry.score, entry.score))
                from_rank, to_score = data
                rank = db.query_one('SELECT COUNT(DISTINCT(score)) AS rank FROM entries WHERE lid=%s AND  %s<score AND score<=%s',
                                   (leaderboard_id, entry.score, to_score))[0]
                entry.rank = from_rank + rank
        return entry


rank
~~~~~


rank算法相对复杂：

.. code-block:: python

    def rank(self, leaderboard_id, limit=1000, offset=0, dense=False):
        from_score, to_score, from_rank, to_rank = db.query_one('SELECT from_score, to_score, from_rank, to_rank FROM chunk_buckets WHERE lid=%s AND from_rank<=%s AND %s<=to_rank', (leaderboard_id, offset+1, offset+1))
        if to_rank < limit + offset + 1:
            from_score = db.query_one('SELECT from_score FROM chunk_buckets WHERE lid=%s AND from_rank<=%s AND %s<=to_rank', (leaderboard_id, limit+offset+1, limit+offset+1))[0]
            
        sql = 'SELECT * FROM entries WHERE lid=%s AND %s<=score AND score<=%s '
        if dense:
            sql += 'ORDER BY score DESC, eid ASC'
        else:
            sql += 'GROUP BY score, eid ORDER BY score DESC'
        sql += ' LIMIT %s OFFSET %s'
        
        res = db.query(sql, (leaderboard_id, from_score, to_score, limit, offset - from_rank+1))
        res = [self._load(data) for data in res]
        if res:
            if not dense:
                entry = self.rank_for_user(leaderboard_id, res[0].entry_id, dense)
                offset = entry.rank
            else:
                offset += 1
            self._rank_entries(res, dense, offset)
        return res

流程与积分桶排差不多：

1. 获取到当前排名范围的积分分布范围
2. 通过缩小积分范围从entries获取到根据积分排序好的用户
3. 然后我们只要获取到第一个用户的排名，然后在业务代码中排好其他用户的名次就行。



均匀区间桶的优点与缺点
~~~~~~~~~~~~~~~~~~~~~~~~~~~

区间桶非常适合那些分用户积分布均匀的排行榜，但要求区间用户数量比较适合比如保证在5000到10000之间排序都是比较高效的。刷新排名时，算法不一定比积分桶慢，但获取用户排名会更慢些。


自适应区间桶
---------------

然后我们考虑下用户的活跃度吧，用户活跃可能非常符合二八法则，或者在某个积分区间的用户量特别大，积分桶和均匀区间桶就都不合适。这时可以考虑使用自适应桶，相对前两者。对于自适应区间的算法就是取出当前最高积分然后使用一个合理阈值得到一个区间，计算该区间的用户数量，如果当前用户数量符合排序的比较快的范围比如[5000, 10000]之间那么，就使用，如果小于5000就增加区间范围，如果大于10000就减少区间范围。区间范围的自适应可以使用指数递半。比如第一次使用[high, low]发现用户量过大，使用low = low + (high - low) / 2 将范围缩小，但这个范围必须保证 high - low 大于等于零，因为等于零时就是退化为积分桶排了，已经不能再小了。反之使用 low = low - (high-low) /2 计算出一个区间，直到找当合适的区间。对于区间多大合适取决于server的硬件性能。


.. note:: 

    因为自适应区间桶的数据存储结构与均匀区间桶是一样的不再表述。


在算法的实现上，如果不做修改，除了sort排序多了自适应区间算法，其他都是一样。这里只稍稍描述下如何做到自适应区间，其他接口请参考均匀区间桶实现。

如何做到自适应区间
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def sort(self, leaderboard_id, chunk_block=CHUNK_BLOCK):
        res = db.query_one('SELECT max(score) as max_score, min(score) as min_score FROM entries WHERE lid=%s', (leaderboard_id,))
        if not res: return
        
        max_score, min_score = res
        rank, dense = 1, 1
        buckets = []
        self.clear_buckets(leaderboard_id)
        to_score = max_score
        chunk = DEFAULT_SCORE_CHUNK
        from_score = to_score - chunk
        from_score = max(min_score, from_score)
        while to_score >= min_score:
            
            # 通过不断获取当前区间的用户数量，找到适合的阈值为止
            while True:
                dense_size = self._get_dense_size(leaderboard_id, from_score, to_score)

                if from_score == 0 or (chunk_block / 2) < dense_size <= chunk_block or chunk == 1:
                    break
                chunk += (chunk / 2) if chunk_block / 2 > dense_size else -(chunk / 2)
                from_score = to_score - chunk

            rank_size = self._get_rank_size(leaderboard_id, from_score,  to_score)
            buckets.append(ChunkBucket(leaderboard_id, from_score, to_score, rank, rank + rank_size - 1, dense, dense + dense_size - 1))
            if len(buckets) == 500:
                self.save_buckets(buckets)
                buckets = []
            to_score = from_score - 1
            from_score = to_score - chunk
            from_score = max(min_score, from_score)
            dense += dense_size
            rank += rank_size

        self.save_buckets(buckets)


均匀区间桶的优点与缺点
~~~~~~~~~~~~~~~~~~~~~~~

对于自适应区间桶，在排序时将会花费更多时间，如果用户的排名实在过于集中，最后局部区间也会退化为积分桶。如果排行规则设计的好，使用户分布比较均匀，那么自适应区间应该是最好的算法。


排行榜刷新重排时需要注意的问题
-------------------------------------



因为桶排需要额外的调用sort方法刷新排行榜，所以需要实现刷新机制，在leaf中使用的mysql做的刷新机制，基本实现了定时刷新，和周期性刷新，以及crontab规则刷新。实现比较简单，可以稍稍看看cron.py中的实现。

细心的会注意到均匀区间桶和自适应桶都是一次性清排行榜的桶数据，而积分桶使用分段先清理老的桶分段数据，然后更新桶信息，确实有必要优化成分段更新，这样能够避免排行榜重排时，一段时间排行榜不可用，或者造成误差很大。在用户更新积分时，排行榜即使没有及时的重排（如果使用其他的排序方法把排名写死，是没法做到这样的变化效果），也能反映出用户的一些排名变化，但积分桶可能不能反映出这种变化。

内存缓存技术
==============


在使用rank api时，很多游戏都更关心top的排行，比如最活跃的一百个工会。这样，可能希望能够保证top排行能够做到实时性。对于桶排来说近似排行会造成不尽人意，这时可以使用内存缓存技术来辅助完成及时排行榜。比如使用Redis来保存排行榜前5000名的活跃用户，这样只要稍稍在用户更新数据时，检查下是否需要更新。但也不一定要使用内存数据库，比如运行的服务不需要考虑分布式集群，那么使用大堆（heap），或者红黑树这些数据结构做个实现，或者集成网络接口作为top排行榜服务，另外使用数据库直排顶部数据有时也是可行的。需要注意的是，在使用mysql这类关联数据库时，rank api会随着offset的增大，拉取数据会变慢，真实性也会降低。


参考 
====

1. `Nagi  -- A Leaderboard System <https://github.com/thomashuang/Nagi>`_
2. `Bucket Sort <http://en.wikipedia.org/wiki/Bucket_sort>`_
3. `Pareto principle <http://en.wikipedia.org/wiki/Pareto_principle>`_
