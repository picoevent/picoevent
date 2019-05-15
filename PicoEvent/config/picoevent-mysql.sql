DROP TABLE IF EXISTS `access_control_list`;
/*!40101 SET @saved_cs_client = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `access_control_list` (
  `id`                bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `event_type_id`     smallint(5) unsigned         DEFAULT NULL,
  `permission`        varchar(255)        NOT NULL,
  `user_id`           int(10) unsigned    NOT NULL,
  `assigned_event_id` bigint(20) unsigned NOT NULL,
  `revoked_event_id`  bigint(20) unsigned          DEFAULT NULL,
  `created`           timestamp           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `event_log_event_type_id_index` (`event_type_id`),
  KEY `event_log_user_id_index` (`user_id`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;


DROP TABLE IF EXISTS `api_keys`;
/*!40101 SET @saved_cs_client = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `api_keys` (
  `node_id`             smallint(5) unsigned                NOT NULL AUTO_INCREMENT,
  `api_key`             VARCHAR(16)                         NOT NULL,
  `created`             timestamp                           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `quota`               int unsigned default '1000'         null,
  `next_reset`          datetime                            null,
  `events_posted`       int unsigned default '0'            null,
  `suspension_event_id` bigint unsigned                     null,
  PRIMARY KEY (`node_id`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `event_log`
--

DROP TABLE IF EXISTS `event_log`;
/*!40101 SET @saved_cs_client = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `event_log` (
  `event_id`      bigint(20) unsigned  NOT NULL AUTO_INCREMENT,
  `event_type_id` smallint(5) unsigned NOT NULL,
  `node_id`       smallint(5) unsigned          DEFAULT NULL,
  `user_id`       int(10) unsigned              DEFAULT NULL,
  `event_data`    LONGTEXT                      DEFAULT NULL,
  `created`       timestamp            NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`event_id`),
  KEY `event_log_event_type_id_index` (`event_type_id`),
  KEY `event_log_user_id_index` (`user_id`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `event_type`
--

DROP TABLE IF EXISTS `event_type`;
/*!40101 SET @saved_cs_client = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `event_type` (
  `event_type_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `event_type`    varchar(55)                   DEFAULT NULL,
  PRIMARY KEY (`event_type_id`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id`           int(10) unsigned NOT NULL AUTO_INCREMENT,
  `email_address`     varchar(55)               DEFAULT NULL,
  `password`          char(64)                  DEFAULT NULL,
  `last_logged_in`    timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP
  ON UPDATE CURRENT_TIMESTAMP,
  `last_logged_in_ip` varchar(15)               DEFAULT NULL,
  `created`           timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_ip`        varchar(15)               DEFAULT NULL,
  `session_token`     char(16)                  DEFAULT NULL,
  `acl`               json                      DEFAULT NULL,
  `full_name`         varchar(255)              DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email_address` (`email_address`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;