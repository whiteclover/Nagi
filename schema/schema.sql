SET @saved_cs_client = @@character_set_client;
SET character_set_client = utf8;

CREATE TABLE `leaderboards` (
  `lid` MEDIUMINT(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(124) NOT NULL,
  `adapter` VARCHAR(16),

  PRIMARY KEY (`lid`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB CHARSET=utf8;

CREATE TABLE `entries` (
  `eid` INT(11) unsigned NOT NULL COMMENT 'The unique identifier for a entry in a leaderboards.',
  `lid` MEDIUMINT(8) unsigned NOT NULL,
  `score` INT(11) unsigned NOT NULL,
  `data` VARCHAR(1024) DEFAULT NULL COMMENT 'THe custom entry data',
  `created` DATETIME NOT NULL DEFAULT NOW() COMMENT 'The DATETIME when the entry was created.',

  PRIMARY KEY (`lid`, `eid`),
  KEY `user_entry` (`lid`, `score`)
) ENGINE=InnoDB CHARSET=utf8;


CREATE TABLE `score_buckets` (
  `lid` MEDIUMINT(8) unsigned NOT NULL,
  `score` INT(11) unsigned NOT NULL,
  `size` INT(11) unsigned NOT NULL,
  `from_dense` INT(11) unsigned NOT NULL,
  `to_dense` INT(11) unsigned NOT NULL,
  `rank` INT(11) unsigned NOT NULL,

  PRIMARY KEY `leaderboard_score` (`lid`, `score`),
  KEY `dense` (`from_dense`, `to_dense`)
) ENGINE=InnoDB CHARSET=utf8;

CREATE TABLE `block_buckets`  (
  `lid` MEDIUMINT(8) unsigned NOT NULL,
  `from_score` INT(11) unsigned NOT NULL,
  `to_score` INT(11) unsigned NOT NULL,
  `from_rank` INT(11) unsigned NOT NULL,
  `to_rank` INT(11) unsigned NOT NULL,
  `from_dense` INT(11) unsigned NOT NULL,
  `to_dense` INT(11) unsigned NOT NULL,

  PRIMARY KEY `leaderboard_score` (`lid`,`from_score`, `to_score`)
) ENGINE=InnoDB CHARSET=utf8;

CREATE TABLE `chunk_buckets`  (
  `lid` MEDIUMINT(8) unsigned NOT NULL,
  `from_score` INT(11) unsigned NOT NULL,
  `to_score` INT(11) unsigned NOT NULL,
  `from_rank` INT(11) unsigned NOT NULL,
  `to_rank` INT(11) unsigned NOT NULL,
  `from_dense` INT(11) unsigned NOT NULL,
  `to_dense` INT(11) unsigned NOT NULL,

  PRIMARY KEY `leaderboard_score` (`lid`,`from_score`, `to_score`)
) ENGINE=InnoDB CHARSET=utf8;

CREATE TABLE `cron` (
  `cron_id` MEDIUMINT(8) unsigned NOT NULL AUTO_INCREMENT,
  `job_id` VARCHAR(64) DEFAULT NULL,
  `name` VARCHAR(124) NOT NULL,
  `event`  VARCHAR(64) NOT NULL,
  `next_run` DATETIME DEFAULT NULL,
  `last_run` DATETIME DEFAULT NULL,
  
  PRIMARY KEY `cron_id` (`cron_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB CHARSET=utf8;


SET @@character_set_client = @saved_cs_client;