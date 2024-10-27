# Left Anti join

A left anti join returns records from the left table that do NOT have matching records in the right table. In other
words, it helps you find records that exist in one table but are missing from another table.

Here's a simple example:

```sql
-- Left Anti join
SELECT a.*
FROM table_a a
LEFT ANTI JOIN table_b b ON a.id = b.id


-- Left anti join using NOT EXISTS
SELECT a.*
FROM table_a a
WHERE NOT EXISTS (
    SELECT 1 
    FROM table_b b 
    WHERE a.id = b.id
);

-- Alternative syntax using LEFT JOIN
SELECT a.*
FROM table_a a
LEFT JOIN table_b b ON a.id = b.id
WHERE b.id IS NULL;
```

Common use cases for left anti join:

1. Finding missing data or gaps:
    - Identifying customers who haven't placed any orders
    - Finding products with no sales
    - Locating employees who haven't completed required training

2. Data quality checks:
    - Finding orphaned records
    - Verifying referential integrity
    - Identifying incomplete data sets

3. Business analysis:
    - Finding inactive customers
    - Identifying products not in current inventory
    - Finding unassigned tasks or resources

## Left out jin vs left anti join

### Left Outer Join:

- Returns ALL records from the left table and matching records from the right table
- If no match exists, NULL values appear for the right table columns
- Useful when you want to see all left table records WITH their corresponding matches (if any)

```sql
-- Left Outer Join example
SELECT employees.name, orders.order_id
FROM employees
LEFT OUTER JOIN orders ON employees.id = orders.employee_id;

-- Results might look like:
-- John    | 101
-- John    | 102
-- Mary    | 103
-- Bob     | NULL    -- Bob has no orders but still appears
```

### Left Anti Join:

- Returns ONLY records from the left table that have NO matches in the right table
- Right table columns are not included in the result
- Useful when you want to find missing or unmatched records

```sql
-- Left Anti Join example
SELECT employees.name
FROM employees
LEFT JOIN orders ON employees.id = orders.employee_id
WHERE orders.employee_id IS NULL;

-- Results might look like:
-- Bob     -- Only Bob appears because he has no orders
```

Key Differences:
1. Result Content:
    - Left Outer: Shows all left records + matching data
    - Left Anti: Shows only unmatched left records

2. Use Cases:
    - Left Outer: When you need a complete view including nulls
    - Left Anti: When you specifically need to find missing relationships

3. Output Columns:
    - Left Outer: Can include columns from both tables
    - Left Anti: Typically only includes left table columns

## When to use - left anti join vs not exists
**Left Anti Join**

1. Multiple Column Comparisons:
```sql
-- More readable with multiple conditions
SELECT a.*
FROM orders a
LEFT JOIN payments b ON 
    a.order_id = b.order_id AND 
    a.customer_id = b.customer_id AND
    a.amount = b.amount
WHERE b.payment_id IS NULL;
```

2. When joining to multiple tables:
```sql
-- Checking against multiple tables
SELECT c.*
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
LEFT JOIN feedback f ON c.id = f.customer_id
WHERE o.order_id IS NULL 
AND f.feedback_id IS NULL;
```

3. When you need additional columns for filtering:
```sql
-- When you need to see other columns for conditions
SELECT a.*
FROM products a
LEFT JOIN sales b ON a.product_id = b.product_id
WHERE b.sale_id IS NULL
AND b.region = 'North';
```

**Use NOT EXISTS when:**

1. Simple Single-Table Checks:
```sql
-- Cleaner for simple existence checks
SELECT c.*
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 
    FROM orders o 
    WHERE c.id = o.customer_id
);
```

2. Performance Critical Operations:
```sql
-- Benefits from early termination
SELECT p.*
FROM products p
WHERE NOT EXISTS (
    SELECT 1 
    FROM inventory i
    WHERE p.product_id = i.product_id
);
```

3. Correlated Subqueries:
```sql
-- More intuitive for correlated subqueries
SELECT e.*
FROM employees e
WHERE NOT EXISTS (
    SELECT 1
    FROM training_completed t
    WHERE e.emp_id = t.emp_id
    AND t.completion_date >= DATEADD(month, -6, GETDATE())
);
```

Key Decision Factors:
1. Query Complexity:
   - Simple checks → NOT EXISTS
   - Complex joins → LEFT ANTI JOIN

2. Readability:
   - Multiple conditions → LEFT ANTI JOIN
   - Single condition → NOT EXISTS

3. Maintenance:
   - Frequently modified queries → LEFT ANTI JOIN (easier to modify)
   - Stable queries → NOT EXISTS (if performance is better)
