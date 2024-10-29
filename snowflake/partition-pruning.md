# Snowflake's partition pruning

1. What is Partition Pruning?

- It's an optimization technique where Snowflake automatically eliminates unnecessary micro-partitions during query
  execution
- Micro-partitions are Snowflake's internal data organization units (approximately 50-500MB compressed)
- It helps improve query performance by scanning only relevant data blocks

2. How Partition Pruning Works:

```sql
-- Example table with date column
CREATE TABLE sales (
    sale_date DATE,
    product_id INT,
    amount DECIMAL(10,2)
);

-- Query that benefits from partition pruning
SELECT SUM(amount) 
FROM sales 
WHERE sale_date >= '2024-01-01' 
AND sale_date < '2024-02-01';
```

The process:

1. Snowflake maintains metadata about value ranges in each micro-partition
2. When a query has a filter (WHERE clause), Snowflake:
    - Checks the min/max values for each column in each micro-partition
    - Skips micro-partitions that can't contain matching data
    - Only scans potentially relevant micro-partitions

3. Clustering Keys vs. Partition Pruning:

```sql
-- Table with clustering key
CREATE TABLE sales_clustered (
    sale_date DATE,
    product_id INT,
    amount DECIMAL(10,2)
) CLUSTER BY (sale_date);

-- Table without clustering key
CREATE TABLE sales_unclustered (
    sale_date DATE,
    product_id INT,
    amount DECIMAL(10,2)
);
```

Important points:

- Partition pruning works WITH or WITHOUT clustering keys
- Clustering keys can make partition pruning more efficient
- Clustering organizes similar data together in micro-partitions

4. Real-world Example Demonstrating Both Cases:

```sql
-- Example showing pruning effectiveness

-- Case 1: Without clustering
CREATE TABLE orders_unclustered (
    order_date DATE,
    customer_id INT,
    amount DECIMAL(10,2)
);

INSERT INTO orders_unclustered 
SELECT 
    DATEADD(day, UNIFORM(1, 365, RANDOM()), '2023-01-01'),
    UNIFORM(1, 1000, RANDOM()),
    UNIFORM(100, 1000, RANDOM())
FROM TABLE(GENERATOR(ROWCOUNT => 1000000));

-- Query to check pruning
SELECT COUNT(*) 
FROM orders_unclustered 
WHERE order_date BETWEEN '2023-06-01' AND '2023-06-30';

-- Case 2: With clustering
CREATE TABLE orders_clustered (
    order_date DATE,
    customer_id INT,
    amount DECIMAL(10,2)
) CLUSTER BY (order_date);

INSERT INTO orders_clustered 
SELECT * FROM orders_unclustered;

-- Same query on clustered table
SELECT COUNT(*) 
FROM orders_clustered 
WHERE order_date BETWEEN '2023-06-01' AND '2023-06-30';
```

5. Monitoring Partition Pruning:

```sql
-- Check pruning effectiveness
SELECT 
    query_id,
    query_text,
    partitions_total,
    partitions_scanned,
    ROUND(100 - (partitions_scanned/partitions_total * 100), 2) as pruning_percentage
FROM table(information_schema.query_history())
WHERE query_text ILIKE '%orders%'
AND partitions_total > 0
ORDER BY start_time DESC
LIMIT 5;
```

6. Best Practices:

```sql
-- Good candidate for pruning
SELECT * 
FROM sales 
WHERE sale_date = '2024-01-01'           -- High pruning potential
AND product_id = 100;

-- Less effective for pruning
SELECT * 
FROM sales 
WHERE MONTH(sale_date) = 1               -- Function on column reduces pruning
AND amount > 1000;                       -- Range condition on non-clustered column
```

Key Takeaways:

1. Partition pruning works automatically in Snowflake
2. No explicit configuration needed
3. Works without clustering, but clustering can improve its effectiveness
4. Most effective with:
    - Equality conditions (=)
    - Range conditions (<, >, BETWEEN)
    - IN lists
    - Direct column references (avoid functions on filtered columns)

Would you like me to show you how to measure the effectiveness of partition pruning for your specific queries or
demonstrate more advanced optimization techniques?


## Question
```text
SELECT SUM(amount) FROM sales WHERE sale_date >= '2024-01-01';
Adding upper bound:
 'and sale_date < '2024-10-28'  
Will adding above upper help in partition pruning even if there is no data  in table for sale_date >= 2024-10-28
```

Yes, adding an upper bound with `sale_date < '2024-10-28'` can help with partition pruning, even if there's no data
beyond that date. Here's why:

1. When Snowflake sees the range condition `sale_date >= '2024-01-01' AND sale_date < '2024-10-28'`:
   - It knows exactly which micro-partitions it needs to scan
   - It can immediately eliminate any micro-partitions with min/max values outside this range
   - The query optimizer has a clear boundary for both ends of the date range

2. Without the upper bound:
   - The condition `sale_date >= '2024-01-01'` creates an open-ended range
   - Snowflake has to check the metadata of all micro-partitions after 2024-01-01
   - Even though there's no data beyond 2024-10-28, Snowflake doesn't know that without checking

Best practices:

- Always specify both lower and upper bounds when possible
- Use semi-open intervals (>= start AND < end) rather than closed intervals
- Keep partition pruning in mind when designing table clustering keys

Your query with both bounds is more efficient:

```sql
SELECT SUM(amount) 
FROM sales 
WHERE sale_date >= '2024-01-01'
AND sale_date < '2024-10-28';
```

