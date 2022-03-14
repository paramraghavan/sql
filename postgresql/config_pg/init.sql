--
-- Table structure for table `Bookings`
--

CREATE TABLE IF NOT EXISTS Bookings (
  bookid INT PRIMARY KEY,
  facid INT ,
  memid INT,
  starttime varchar(19),
  slots INT
);


CREATE TABLE IF NOT EXISTS Facilities (
  facid INT  PRIMARY KEY,
  name varchar(15),
  membercost decimal(2,1),
  guestcost decimal(3,1),
  initialoutlay INT,
  monthlymaintenance INT
);

--
-- Table structure for table `Members`
--

CREATE TABLE IF NOT EXISTS Members (
  memid INT  PRIMARY KEY,
  surname varchar(17),
  firstname varchar(9),
  address varchar(39),
  zipcode INT,
  telephone varchar(14),
  recommendedby varchar(2),
  joindate varchar(19)
);


--
-- Create table runners
--
CREATE TABLE IF NOT EXISTS Runners (
  id INT  PRIMARY KEY,
  name varchar(17),
  weight decimal,
  country varchar(17),
  time INT
);

CREATE TABLE categories
( category_id INT PRIMARY KEY,
  category_name char(50) NOT NULL
);

--
-- Joins
--
CREATE TABLE customers
( customer_id INT PRIMARY KEY ,
  last_name char(50) NOT NULL,
  first_name char(50) NOT NULL,
  favorite_website char(50)
);

CREATE TABLE departments
( dept_id INT  PRIMARY KEY,
  dept_name char(50) NOT NULL
);

CREATE TABLE employees
( employee_number INT PRIMARY KEY ,
  last_name char(50) NOT NULL,
  first_name char(50) NOT NULL,
  salary INT,
  dept_id INT
);

CREATE TABLE orders
( order_id INT PRIMARY KEY ,
  customer_id INT,
  order_date date
);

CREATE TABLE products
( product_id INT PRIMARY KEY ,
  product_name char(50) NOT NULL,
  category_id INT
);

CREATE TABLE suppliers
( supplier_id INT ,
  supplier_name char(50) NOT NULL,
  city char(50),
  state char(50),
  CONSTRAINT suppliers_pk PRIMARY KEY (supplier_id)
);

COPY bookings(bookid,facid,memid,starttime,slots)
FROM '/tmp/bookings.csv' DELIMITER ',' CSV HEADER;

COPY categories(category_id,category_name)
FROM '/tmp/categories.csv' DELIMITER ',' CSV HEADER;

COPY customers(customer_id,last_name,first_name,favorite_website)
FROM '/tmp/customers.csv' DELIMITER ',' CSV HEADER;

COPY departments(dept_id,dept_name)
FROM '/tmp/departments.csv' DELIMITER ',' CSV HEADER;

COPY employees(employee_number,last_name,first_name,salary,dept_id)
FROM '/tmp/employees.csv' DELIMITER ',' CSV HEADER;

COPY facilities(facid,name,membercost,guestcost,initialoutlay,monthlymaINTenance)
FROM '/tmp/facilities.csv' DELIMITER ',' CSV HEADER;

COPY members(memid,surname,firstname,address,zipcode,telephone,recommendedby,joindate)
FROM '/tmp/members.csv' DELIMITER ',' CSV HEADER;

COPY orders(order_id,customer_id,order_date)
FROM '/tmp/orders.csv' DELIMITER ',' CSV HEADER;

COPY products(product_id,product_name,category_id)
FROM '/tmp/products.csv' DELIMITER ',' CSV HEADER;

COPY runners(id,name,weight,country,time)
FROM '/tmp/runners.csv' DELIMITER ',' CSV HEADER;

COPY suppliers(supplier_id,supplier_name,city,state)
FROM '/tmp/suppliers.csv' DELIMITER ',' CSV HEADER;


--CREATE TABLE students (
--    id SERIAL PRIMARY KEY,
--    fname character varying(255),
--    lname character varying(255),
--    email character varying(255),
--    ssn character varying(255),
--    address character varying(255),
--    cid character varying(255)
--);


--
--COPY students(id, fname, lname, email, ssn, address, cid)
--FROM '/tmp/students.csv' DELIMITER '_' CSV HEADER;