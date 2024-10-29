# The most effective ways to optimize large table joins in Snowflake are:

* Ensure proper clustering on join keys
* Use appropriate join types (prefer INNER over LEFT when possible)
* Filter data before joining
* Consider materialized views for frequently joined data


# Monitor snowflake query performance

```sql
-- Monitor execution time and resources
SELECT 
    query_id,
    total_elapsed_time/1000 as execution_time_seconds,
    bytes_scanned/power(1024,3) as gb_scanned,
    percentage_scanned_from_cache
FROM table(information_schema.query_history())
WHERE query_text LIKE '%new_record_table%'
ORDER BY start_time DESC;
```

* Run ANALYZE TABLE on all tables periodically to update statistics
* Consider partitioning the history table if it has a natural partition key
* Use EXPLAIN PLAN to understand query execution and identify bottlenecks
* Monitor cache hit ratios and adjust clustering keys if needed

## Table Size Analysis & Optimization Strategy
* List your table sizes

## Data Pruning & Join Optimization:

## clustering
- [clustering](clustering-vs-indexexing.md)

## REsource and session optimization
```sql
-- Set optimal warehouse configuration
CREATE OR REPLACE WAREHOUSE load_warehouse WITH
    WAREHOUSE_SIZE = 'LARGE'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- Optimize session parameters
ALTER SESSION SET
    USE_CACHED_RESULT = TRUE,
    QUERY_ACCELERATION_MAX_SCALE_FACTOR = 8,
    JDBC_QUERY_RESULT_FORMAT = 'ARROW',
    STATEMENT_TIMEOUT_IN_SECONDS = 3600;
```

