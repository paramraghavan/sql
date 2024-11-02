# Snowflake Performance Guide for RDBMS Developers

## 1. Key Paradigm Shifts

### Traditional RDBMS vs Snowflake

- **Storage**: Column-oriented vs row-oriented
- **Resources**: Virtual warehouses vs server resources
- **Scaling**: Automatic vs manual configuration
- **Caching**: Result caching vs buffer cache
- **Cost Model**: Compute time vs server capacity

## 2. Virtual Warehouse Best Practices

### Sizing Guidelines

```sql
-- Start with smaller warehouse and scale up as needed
CREATE WAREHOUSE IF NOT EXISTS dev_warehouse WITH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300  -- Suspend after 5 minutes of inactivity
  AUTO_RESUME = true
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3;

-- Monitor warehouse usage
SELECT * FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START=>DATEADD('days',-7,CURRENT_DATE()),
    DATE_RANGE_END=>CURRENT_DATE()));
```

### Multi-Cluster Configuration

```sql
-- For handling concurrent queries
ALTER WAREHOUSE dev_warehouse SET
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3
  SCALING_POLICY = 'STANDARD';
```

## 3. Performance Optimization Techniques

### 1. Query Performance

#### Clustering Keys

```sql
-- Examine clustering depth
SELECT SYSTEM$CLUSTERING_DEPTH('YOUR_TABLE');

-- Create clustering key
ALTER TABLE your_table
CLUSTER BY (date_column, category_column);

-- Monitor clustering
SELECT SYSTEM$CLUSTERING_INFORMATION('your_table');
```

#### Materialized Views

```sql
-- Create materialized view for common aggregations
CREATE MATERIALIZED VIEW daily_sales AS
SELECT 
    date_trunc('day', sale_timestamp) as sale_date,
    product_id,
    sum(amount) as total_amount,
    count(*) as transaction_count
FROM sales
GROUP BY 1, 2;
```

### 2. Data Loading Optimization

#### Bulk Loading

```sql
-- Create file format
CREATE OR REPLACE FILE FORMAT csv_format
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    NULL_IF = ('NULL', 'null')
    EMPTY_FIELD_AS_NULL = true;

-- Create stage
CREATE OR REPLACE STAGE my_stage
    FILE_FORMAT = csv_format;

-- Efficient copy command
COPY INTO my_table
FROM @my_stage/data/
PATTERN = '.*\.csv\.gz'
ON_ERROR = 'CONTINUE'
SIZE_LIMIT = 16777216;
```

### 3. Data Processing Patterns

#### Micro-batching

```sql
-- Process data in micro-batches
CREATE OR REPLACE PROCEDURE process_data_in_batches()
RETURNS string
LANGUAGE javascript
AS
$$
    var batch_size = 100000;
    var processed = 0;
    
    do {
        var stmt = snowflake.createStatement({
            sqlText: `
                WITH batch AS (
                    SELECT id 
                    FROM unprocessed_data 
                    WHERE processed = false 
                    LIMIT ?
                )
                UPDATE unprocessed_data SET
                    processed = true
                WHERE id IN (SELECT id FROM batch)
                RETURNING COUNT(*)`
            ,
            binds: [batch_size]
        });
        
        var result = stmt.execute();
        result.next();
        processed = result.getColumnValue(1);
        
    } while (processed > 0);
    
    return 'Processing completed';
$$;
```

### 4. Performance Monitoring

#### Query Profile Analysis

```sql
-- Get query history with execution details
SELECT 
    query_id,
    query_text,
    warehouse_size,
    execution_time,
    bytes_scanned,
    percentage_scanned_from_cache
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE execution_time > 1000  -- queries taking more than 1 second
ORDER BY start_time DESC
LIMIT 100;
```

## 5. Cost Optimization Techniques

### Resource Optimization

```sql
-- Set resource monitors
CREATE RESOURCE MONITOR dev_monitor
WITH 
    CREDIT_QUOTA = 100      -- Maximum credits
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS 
        ON 75 PERCENT DO NOTIFY
        ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE dev_warehouse SET
    RESOURCE_MONITOR = 'dev_monitor';
```

### Query Cost Analysis

```sql
-- Analyze query costs
SELECT 
    warehouse_name,
    COUNT(*) as query_count,
    AVG(execution_time)/1000 as avg_execution_seconds,
    SUM(credits_used) as total_credits
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START=>DATEADD('days',-30,CURRENT_DATE()),
    DATE_RANGE_END=>CURRENT_DATE()))
GROUP BY 1
ORDER BY 4 DESC;
```

## 6. Development Best Practices

### 1. Zero-Copy Cloning

```sql
-- Create development environments quickly
CREATE DATABASE dev_db CLONE prod_db;
CREATE TABLE dev_table CLONE prod_table;
```

### 2. Time Travel Operations

```sql
-- Query historical data
SELECT * FROM my_table AT(OFFSET => -60*60);  -- 1 hour ago
SELECT * FROM my_table BEFORE(STATEMENT => '<query_id>');

-- Restore accidentally deleted data
CREATE TABLE recovered_table CLONE my_table AT(OFFSET => -60*5);
```

### 3. Session Management

```sql
-- Configure session parameters
ALTER SESSION SET 
    QUERY_TAG = 'development',
    TIMESTAMP_OUTPUT_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF',
    TIMEZONE = 'UTC',
    USE_CACHED_RESULT = true;
```

## 7. Common Performance Pitfalls

1. **Anti-Patterns to Avoid**
    - Using small transaction sizes
    - Ignoring clustering keys
    - Not leveraging caching
    - Inappropriate warehouse sizing
    - Running analytics on XSMALL warehouses

2. **Better Alternatives**
    - Batch operations
    - Use appropriate clustering keys
    - Leverage result caching
    - Right-size warehouses
    - Use larger warehouses for analytics

## 8. Monitoring and Optimization

```sql
-- Create performance monitoring view
CREATE OR REPLACE VIEW v_performance_metrics AS
SELECT 
    date_trunc('hour', start_time) as time_bucket,
    warehouse_name,
    COUNT(*) as query_count,
    AVG(execution_time)/1000 as avg_execution_seconds,
    SUM(bytes_scanned)/POWER(1024, 3) as gb_scanned,
    AVG(percentage_scanned_from_cache) as cache_hit_ratio
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE start_time >= dateadd('day', -7, current_timestamp())
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```