The db file --> ql\sqlDB\sqlite_db_pythonsqlite.db, has the "country_club" database. This database
contains 3 tables:
1. the "Bookings" table,
2. the "Facilities" table, and
3. the "Members" table.

--
--   If you ever want to create and upload data again, drop database and create a new database via DB Browser SQLite
--   - github\sql\sqlDB\create_table.sql
--   - github\sql\sqlDB\insert_rows.sql
--

--    Before starting with the questions, feel free to take your time,
--    exploring the data, and getting acquainted with the 3 tables. Open db browser
--    lite, File --> Open Databasr -->sql\sqlDB\sqlite_db_pythonsqlite.db


/* QUESTIONS 
/* Q1: Some of the facilities charge a fee to members, but some do not.
Write a SQL query to produce a list of the names of the facilities that do. */

select name from Facilities where membercost <> 0;

/* Q2: How many facilities do not charge a fee to members? */

select count(*) from Facilities where membercost = 0

/* Q3: Write an SQL query to show a list of facilities that charge a fee to members,
where the fee is less than 20% of the facility's monthly maintenance cost.
Return the facid, facility name, member cost, and monthly maintenance of the
facilities in question. */

SELECT facid, name, membercost, monthlymaintenance, 
monthlymaintenance*0.2 percentratio
FROM Facilities
WHERE membercost < (monthlymaintenance * 0.2)  
AND membercost <> 0
 

/* Q4: Write an SQL query to retrieve the details of facilities with ID 1 and 5.
Try writing the query without using the OR operator. */

SELECT * 
FROM Facilities
where facid in (1,5)

/* Q5: Produce a list of facilities, with each labelled as
'cheap' or 'expensive', depending on if their monthly maintenance cost is
more than $100. Return the name and monthly maintenance of the facilities
in question. */

SELECT name,
CASE WHEN monthlymaintenance >100
THEN 'Expensive'
ELSE 'Cheap'
END
FROM Facilities

/* Q6: You'd like to get the first and last name of the last member(s)
who signed up. Try not to use the LIMIT clause for your solution. */

SELECT firstname, surname
FROM Members
WHERE joindate = (
SELECT MAX( joindate )
FROM Members )

OR

SELECT firstname, surname
FROM Members
order by joindate desc limit 1

/* Q7: Produce a list of all members who have used a tennis court.
Include in your output the name of the court, and the name of the member
formatted as a single column. Ensure no duplicate data, and order by
the member name. */

SELECT DISTINCT f.name courtname, CONCAT( firstname, ' ', surname ) membername
FROM Bookings b
LEFT JOIN Members m ON b.memid = m.memid
LEFT JOIN Facilities f ON b.facid = f.facid
WHERE f.name LIKE 'Tennis Court%'
ORDER BY membername


/* Q8: Produce a list of bookings on the day of 2012-09-14 which
will cost the member (or guest) more than $30. Remember that guests have
different costs to members (the listed costs are per half-hour 'slot'), and
the guest user's ID is always 0. Include in your output the name of the
facility, the name of the member formatted as a single column, and the cost.
Order by descending cost, and do not use any subqueries. */

--SELECT f.name facilityname, CONCAT( firstname, ' ', surname ) membername,
SELECT f.name facilityname, firstname || ' ' || surname as  membername,
CASE WHEN m.firstname = 'GUEST'
THEN guestcost * slots
ELSE membercost * slots
END AS cost
FROM Bookings b
INNER JOIN Members m ON b.memid = m.memid
INNER JOIN Facilities f ON b.facid = f.facid
--WHERE DATE_FORMAT( starttime, '%Y-%m-%d' ) = '2012-09-14'
WHERE strftime('%Y-%m-%d',starttime) = '2012-09-14'
AND CASE WHEN m.firstname = 'GUEST'
THEN guestcost * slots >30
ELSE membercost * slots >30
END
ORDER BY cost DESC

/* Q9: This time, produce the same result as in Q8, but using a subquery. */

SELECT facilityname, CONCAT( firstname, ' ', surname ) membername, cost
FROM (
SELECT firstname, surname,
CASE WHEN m.firstname = 'GUEST'
THEN guestcost * slots
ELSE membercost * slots
END AS cost, f.name facilityname
FROM Bookings b
INNER JOIN Members m ON b.memid = m.memid
INNER JOIN Facilities f ON b.facid = f.facid
WHERE DATE_FORMAT( starttime, '%Y-%m-%d' ) = '2012-09-14'
)a
WHERE cost >30
ORDER BY cost DESC

/* PART 2: SQLite

QUESTIONS:
/* Q10: Produce a list of facilities with a total revenue less than 1000.
The output of facility name and total revenue, sorted by revenue. Remember
that there's a different 	cost for guests and members! */

WITH fac_details AS (select f.facid, f.name facilityname, 
CASE WHEN m.firstname = 'GUEST'
    THEN guestcost * slots
    ELSE membercost * slots
    END AS cost
from Bookings b
INNER JOIN Members m ON b.memid = m.memid
inner join Facilities f on b.facid = f.facid)

select * from 
(select facilityname, sum(fac_details.cost) totalrevenue
from fac_details
group by facid)
where totalrevenue < 1000

/* OR */

WITH fac_details AS(
Select b.facid, b.memid, b.starttime, b.slots,  m.firstname, f.name as facility_name,
CASE WHEN m.firstname = 'GUEST'
THEN f.guestcost * b.slots
ELSE f.membercost * b.slots
END AS cost
from
Bookings b
LEFT join Facilities f ON b.facid = f.facid
LEFT join Members m ON m.memid = b.memid
)

select facility_name, sum(cost) as totalrevenue from fac_details
group by facility_name having totalrevenue >1000

--select f.name, f.facid, f.membercost, f.guestcost from Facilities f;
--Select m.memid, m.firstname from Members m4

/* Q11: Produce a report of members and who recommended them in alphabetic surname,firstname order */

select m1.surname || ' ' || m1.firstname membername, 
m2.surname ||' ' || m2.firstname recommendedBy
from members m1
inner join members m2 on m1.recommendedby = m2.memid
order by m1.surname, m1.firstname

/* Q12: Find the facilities with their usage by member, but not guests */


how many times it got booked -like sum of slots

    select name, usage 
    from Facilities f
    inner join (SELECT facid, sum(slots) usage
        FROM Bookings b, Members m
        where b.facid = m.memid
        and m.firstname <> 'GUEST'
        group by facid) a
      where f.facid = a.facid


/* Q13: Find the facilities usage by month, but not guests */

facid, month , slots total
/* EXTRACT and date_format did not work in jupyternotebook */

select name, month, usage 
    from Facilities f
    inner join (SELECT facid, strftime("%m", starttime) month, sum(slots) usage
        FROM Bookings b left join Members m
        ON b.facid = m.memid
        and m.firstname <> 'GUEST'
        group by facid, month) a
      where f.facid = a.facid


WITH fac_details AS (select f.facid, f.name facilityname, 
CASE WHEN m.firstname = 'GUEST'
    THEN guestcost * slots
    ELSE membercost * slots
    END AS cost
from Bookings b
INNER JOIN Members m ON b.memid = m.memid
inner join Facilities f on b.facid = f.facid)

select * from 
(select facilityname, sum(fac_details.cost) totalrevenue
from fac_details
group by facid)
where totalrevenue < 1000

