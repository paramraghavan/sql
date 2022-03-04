--
-- Table structure for table `Bookings`
--

CREATE TABLE IF NOT EXISTS `Bookings` (
  `bookid` int(4) NOT NULL DEFAULT '0',
  `facid` int(1) DEFAULT NULL,
  `memid` int(2) DEFAULT NULL,
  `starttime` varchar(19) DEFAULT NULL,
  `slots` int(2) DEFAULT NULL,
  PRIMARY KEY (`bookid`)
);


CREATE TABLE IF NOT EXISTS `Facilities` (
  `facid` int(1) NOT NULL DEFAULT '0',
  `name` varchar(15) DEFAULT NULL,
  `membercost` decimal(2,1) DEFAULT NULL,
  `guestcost` decimal(3,1) DEFAULT NULL,
  `initialoutlay` int(5) DEFAULT NULL,
  `monthlymaintenance` int(4) DEFAULT NULL,
  PRIMARY KEY (`facid`)
);

--
-- Table structure for table `Members`
--

CREATE TABLE IF NOT EXISTS `Members` (
  `memid` int(2) NOT NULL DEFAULT '0',
  `surname` varchar(17) DEFAULT NULL,
  `firstname` varchar(9) DEFAULT NULL,
  `address` varchar(39) DEFAULT NULL,
  `zipcode` int(5) DEFAULT NULL,
  `telephone` varchar(14) DEFAULT NULL,
  `recommendedby` varchar(2) DEFAULT NULL,
  `joindate` varchar(19) DEFAULT NULL,
  PRIMARY KEY (`memid`)
);


commit;

