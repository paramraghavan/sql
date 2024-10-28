# Snowflake's partition pruning

Snowflake skips partition pruning, as this is crucial for query optimization.



```sql
-- Setup example table with clustering
CREATE OR REPLACE TABLE sales_data (
    sale_date DATE,
    region VARCHAR,
    product_category VARCHAR,
    amount DECIMAL(12,2),
    customer_id INT,
    last_update_time TIMESTAMP
)
CLUSTER BY (sale_date, region);

-- 1. Functions on Clustered Columns
-- Pruning SKIPPED: Function wrapped around clustered column
SELECT SUM(amount)
FROM sales_data
WHERE DATE_TRUNC('month', sale_date) = '2024-01-01';

-- Pruning WORKS: Direct comparison
SELECT SUM(amount)
FROM sales_data
WHERE sale_date >= '2024-01-01' AND sale_date < '2024-02-01';

-- 2. Type Casting Issues
-- Pruning SKIPPED: Implicit casting
SELECT * FROM sales_data
WHERE sale_date = '20240101';

-- Pruning WORKS: Proper date format
SELECT * FROM sales_data
WHERE sale_date = DATE('2024-01-01');

-- 3. OR Conditions Spanning Partitions
-- Pruning SKIPPED: OR condition across clustered columns
SELECT * FROM sales_data
WHERE region = 'EAST' OR sale_date >= '2024-01-01';

-- Pruning WORKS: Separate UNION ALL
SELECT * FROM sales_data WHERE region = 'EAST'
UNION ALL
SELECT * FROM sales_data WHERE sale_date >= '2024-01-01';

-- 4. Complex Expressions
-- Pruning SKIPPED: Complex calculation on clustered column
SELECT * FROM sales_data
WHERE DATEDIFF('day', sale_date, CURRENT_DATE()) < 30;

-- Pruning WORKS: Simplified equivalent
SELECT * FROM sales_data
WHERE sale_date >= DATEADD('day', -30, CURRENT_DATE());

-- 5. Correlated Subqueries
-- Pruning SKIPPED: Correlated subquery on clustered column
SELECT * FROM sales_data s1
WHERE EXISTS (
    SELECT 1 FROM sales_data s2
    WHERE s2.sale_date = s1.sale_date
    AND s2.amount > 1000
);

-- 6. Dynamic SQL/Variables
-- Pruning might be SKIPPED: Dynamic SQL
SET my_date = '2024-01-01';
SELECT * FROM sales_data
WHERE sale_date = $my_date;

-- 7. Non-SARGable Conditions
-- Pruning SKIPPED: Non-SARGable condition
SELECT * FROM sales_data
WHERE region LIKE '%EST%';

-- Pruning WORKS: SARGable condition
SELECT * FROM sales_data
WHERE region LIKE 'WEST%';

-- Monitoring Query to Check Partition Pruning
SELECT 
    query_id,
    query_text,
    partitions_scanned,
    partitions_total,
    ROUND(partitions_scanned::float / NULLIF(partitions_total, 0) * 100, 2) as partition_scan_ratio,
    execution_time,
    bytes_scanned
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE query_text ILIKE '%sales_data%'
    AND start_time >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

```

Here are the main scenarios where Snowflake skips partition pruning:

1. Function Wrapping:
   - Using functions on clustered/prunable columns
   - Example: `DATE_TRUNC(sale_date)` instead of direct comparison
   - Solution: Rewrite queries to avoid functions on filtered columns

2. Data Type Issues:
   - Implicit type casting
   - Mismatched data types in comparisons
   - Solution: Use explicit casting and proper data types

3. Complex Predicates:
   - OR conditions spanning multiple partitions
   - Complex mathematical expressions
   - Solution: Rewrite using UNION ALL or simplify expressions

4. Non-SARGable Conditions:
   - Leading wildcards in LIKE conditions
   - Calculations or transformations on columns
   - Solution: Use proper indexable conditions

5. Correlated Subqueries:
   - When clustered columns are used in correlated subqueries
   - Solution: Rewrite using joins when possible

6. Dynamic SQL Limitations:
   - Variables in WHERE clauses might bypass pruning
   - Solution: Use proper data types and explicit conversions

7. Other Common Cases:
   - Regular expressions on clustered columns
   - User-defined functions (UDFs)
   - Complex CASE expressions on clustered columns

Best Practices to Maintain Pruning:
1. Use direct comparisons on clustered columns
2. Avoid functions or transformations on filtered columns
3. Monitor query profiles for partition scanning
4. Rewrite queries to leverage pruning when possible
5. Use appropriate data types and explicit casting

 # Analyze if specific queries are using partition pruning effectively
 I'll show you how to analyze partition pruning effectiveness for your queries using different Snowflake tools and functions.

```sql
-- 1. Query Profile Analysis
-- Run your query with EXPLAIN PLAN
EXPLAIN
SELECT SUM(amount)
FROM sales_transactions
WHERE transaction_date >= '2024-01-01'
AND store_id = 100;

-- 2. Detailed Query History Analysis
SELECT 
    query_id,
    query_text,
    partitions_scanned,
    partitions_total,
    ROUND(100 * partitions_scanned/NULLIF(partitions_total,0), 2) as partition_scan_percentage,
    ROUND(bytes_scanned/1024/1024/1024, 2) as gb_scanned,
    ROUND(execution_time/1000, 2) as execution_time_seconds,
    start_time
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE query_text ILIKE '%sales_transactions%'
    AND start_time >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- 3. Partition Metadata Analysis
WITH partition_stats AS (
    SELECT 
        partition_number,
        MIN(transaction_date) as min_date,
        MAX(transaction_date) as max_date,
        COUNT(*) as row_count,
        SUM(CASE WHEN store_id = 100 THEN 1 ELSE 0 END) as store_100_rows
    FROM sales_transactions
    GROUP BY 1
)
SELECT 
    partition_number,
    min_date,
    max_date,
    row_count,
    store_100_rows,
    ROUND(100.0 * store_100_rows / row_count, 2) as store_100_percentage
FROM partition_stats
ORDER BY partition_number;

-- 4. Clustering Analysis for Partitioned Columns
SELECT SYSTEM$CLUSTERING_INFORMATION(
    'sales_transactions',
    '(transaction_date, store_id)'
);

-- 5. Query Pattern Analysis Over Time
WITH query_metrics AS (
    SELECT 
        DATE_TRUNC('hour', start_time) as hour,
        COUNT(*) as query_count,
        AVG(partitions_scanned) as avg_partitions_scanned,
        AVG(partitions_total) as avg_partitions_total,
        AVG(bytes_scanned) as avg_bytes_scanned,
        AVG(execution_time) as avg_execution_time
    FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
    WHERE query_text ILIKE '%sales_transactions%'
        AND start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
    GROUP BY 1
)
SELECT 
    hour,
    query_count,
    ROUND(avg_partitions_scanned, 0) as avg_partitions_scanned,
    ROUND(100 * avg_partitions_scanned/NULLIF(avg_partitions_total,0), 2) as avg_partition_scan_percentage,
    ROUND(avg_bytes_scanned/1024/1024/1024, 2) as avg_gb_scanned,
    ROUND(avg_execution_time/1000, 2) as avg_execution_time_seconds
FROM query_metrics
ORDER BY hour DESC;

-- 6. Create Monitoring View for Ongoing Analysis
CREATE OR REPLACE VIEW partition_pruning_monitor AS
WITH base_metrics AS (
    SELECT 
        query_id,
        query_text,
        partitions_scanned,
        partitions_total,
        bytes_scanned,
        execution_time,
        start_time,
        REGEXP_SUBSTR(query_text, 'FROM\\s+([\\w\\.$_]+)', 1, 1, 'i', 1) as table_name
    FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
    WHERE start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP())
)
SELECT 
    table_name,
    COUNT(*) as query_count,
    AVG(partitions_scanned) as avg_partitions_scanned,
    AVG(partitions_total) as avg_partitions_total,
    ROUND(100 * AVG(partitions_scanned)/NULLIF(AVG(partitions_total),0), 2) as avg_partition_scan_percentage,
    ROUND(AVG(bytes_scanned)/1024/1024/1024, 2) as avg_gb_scanned,
    ROUND(AVG(execution_time)/1000, 2) as avg_execution_time_seconds,
    MIN(start_time) as first_query,
    MAX(start_time) as last_query
FROM base_metrics
WHERE table_name IS NOT NULL
GROUP BY 1
ORDER BY avg_gb_scanned DESC;

```

Here's how to interpret and use these analysis tools:

1. Query-Level Analysis:
   - Check EXPLAIN PLAN output for:
     * Partition pruning indicators
     * Number of partitions being scanned
     * Filter pushdown information

2. Performance Metrics to Monitor:
   - Partition scan ratio (partitions_scanned/partitions_total)
     * Good: < 20% of partitions scanned
     * Warning: 20-50% partitions scanned
     * Poor: > 50% partitions scanned
   
   - Bytes scanned
     * Indicates actual data read
     * High values suggest poor pruning

3. Red Flags in Analysis:
   - High partition scan percentages
   - Consistent full table scans
   - Large variations in execution time
   - High bytes scanned for simple queries

4. What to Look For:
   ```sql
   -- Poor pruning example (high partition scan %)
   WHERE YEAR(date_column) = 2024  -- Function prevents pruning
   
   -- Good pruning example (low partition scan %)
   WHERE date_column >= '2024-01-01' 
   AND date_column < '2025-01-01'
   ```

5. Optimization Steps Based on Analysis:
   a. If seeing high partition scanning:
      - Review WHERE clauses
      - Check for function usage
      - Verify data types
   
   b. If seeing poor clustering:
      - Consider reclustering
      - Review clustering keys
   
   c. If seeing inconsistent performance:
      - Check for concurrent loads
      - Monitor resource contention
