--
-- Table structure for table `companies`
--

DROP TABLE IF EXISTS `companies`;
CREATE TABLE `companies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` mediumtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` mediumtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `logo` mediumtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hq_position` bigint(20) DEFAULT NULL,
  `founder` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `net_worth` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `founder` (`founder`),
  CONSTRAINT `companies_ibfk_1` FOREIGN KEY (`founder`) REFERENCES `players` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
CREATE TABLE `jobs` (
  `player_id` varchar(255) NOT NULL,
  `place_to` bigint(20) DEFAULT NULL,
  `place_from` bigint(20) DEFAULT NULL,
  `state` int(11) DEFAULT NULL,
  `reward` int(11) DEFAULT NULL,
  `create_time` int(11) DEFAULT NULL,
  PRIMARY KEY (`player_id`),
  UNIQUE KEY `player_id` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `players`
--

DROP TABLE IF EXISTS `players`;
CREATE TABLE `players` (
  `id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `discriminator` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `xp` int(11) DEFAULT NULL,
  `money` int(11) DEFAULT NULL,
  `position` bigint(20) DEFAULT NULL,
  `miles` int(11) DEFAULT NULL,
  `truck_miles` int(11) DEFAULT NULL,
  `gas` int(11) DEFAULT NULL,
  `truck_id` int(11) DEFAULT NULL,
  `loaded_items` mediumtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `company` int(11) DEFAULT NULL,
  `last_vote` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `company` (`company`),
  CONSTRAINT `players_ibfk_1` FOREIGN KEY (`company`) REFERENCES `companies` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
