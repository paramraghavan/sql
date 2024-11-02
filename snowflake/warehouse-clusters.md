# Snowflake Warehouse Configuration Guide

## 1. Warehouse Sizes

### Available Sizes

- X-Small (XSMALL): 1 credit/hour
- Small (SMALL): 2 credits/hour
- Medium (MEDIUM): 4 credits/hour
- Large (LARGE): 8 credits/hour
- X-Large (XLARGE): 16 credits/hour
- 2X-Large (2XLARGE): 32 credits/hour
- 3X-Large (3XLARGE): 64 credits/hour
- 4X-Large (4XLARGE): 128 credits/hour

- example calculating credits
```sql
-- Development Warehouse (XSMALL)
CREATE WAREHOUSE dev_wh WITH
    WAREHOUSE_SIZE = 'XSMALL'   -- 1 credit/hour
    AUTO_SUSPEND = 300;         -- Suspends after 5 minutes of inactivity
-- If used 4 hours/day with 50% activity:
-- 1 credit/hour × 4 hours × 0.5 = 2 credits/day

-- Production ETL (MEDIUM, 2 clusters)
CREATE WAREHOUSE etl_wh WITH
    WAREHOUSE_SIZE = 'MEDIUM'   -- 4 credits/hour
    MIN_CLUSTER_COUNT = 2;      -- 8 credits/hour total
-- If running for 2 hours:
-- 8 credits/hour × 2 hours = 16 credits
```


### Size Selection Guidelines

1. **XSMALL - SMALL**
    - Interactive queries and development
    - Small data transformations (<100GB)
    - Simple reporting queries
   ```sql
   CREATE WAREHOUSE dev_wh WITH
     WAREHOUSE_SIZE = 'XSMALL'
     AUTO_SUSPEND = 300
     AUTO_RESUME = true;
   ```

2. **MEDIUM - LARGE**
    - Production ETL workloads
    - Complex reporting queries
    - Data transformations (100GB-1TB)
   ```sql
   CREATE WAREHOUSE prod_etl_wh WITH
     WAREHOUSE_SIZE = 'MEDIUM'
     AUTO_SUSPEND = 600
     AUTO_RESUME = true;
   ```

3. **XLARGE - 2XLARGE**
    - Large-scale data processing
    - Complex analytics
    - Data transformations (>1TB)
   ```sql
   CREATE WAREHOUSE analytics_wh WITH
     WAREHOUSE_SIZE = 'XLARGE'
     AUTO_SUSPEND = 900
     AUTO_RESUME = true;
   ```

4. **3XLARGE - 4XLARGE**
    - Massive parallel processing
    - Time-critical large data operations
    - Enterprise data warehouse migrations
   ```sql
   CREATE WAREHOUSE enterprise_wh WITH
     WAREHOUSE_SIZE = 'XXLARGE'
     AUTO_SUSPEND = 1200
     AUTO_RESUME = true;
   ```

## 2. Multi-Cluster Configuration

### Cluster Counts

```sql
-- Basic multi-cluster setup
CREATE WAREHOUSE multi_cluster_wh WITH
  WAREHOUSE_SIZE = 'MEDIUM'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3
  SCALING_POLICY = 'STANDARD'
  AUTO_SUSPEND = 300
  AUTO_RESUME = true;
```

### Scaling Behaviour
```text
Scenario 1: Light Load
- Active Clusters: 1
- Credit Usage: 4 credits/hour
- Status: Baseline operation

Scenario 2: Medium Load
- Active Clusters: 2
- Credit Usage: 8 credits/hour
- Trigger: Query queuing or longer execution times

Scenario 3: Heavy Load
- Active Clusters: 3
- Credit Usage: 12 credits/hour
- Trigger: Continued high demand

```

### Scaling Policies

1. **STANDARD**
    - Adds clusters based on queue depth
    - Best for normal workloads
   ```sql
   ALTER WAREHOUSE multi_cluster_wh SET
     SCALING_POLICY = 'STANDARD';
   ```

2. **ECONOMY**
    - More conservative scaling
    - Waits longer before adding clusters
   ```sql
   ALTER WAREHOUSE multi_cluster_wh SET
     SCALING_POLICY = 'ECONOMY';
   ```

### Common Multi-Cluster Patterns

1. **Development Environment**
   ```sql
   CREATE WAREHOUSE dev_multi_wh WITH
     WAREHOUSE_SIZE = 'SMALL'
     MIN_CLUSTER_COUNT = 1
     MAX_CLUSTER_COUNT = 2
     SCALING_POLICY = 'ECONOMY'
     AUTO_SUSPEND = 300
     AUTO_RESUME = true;
   ```

2. **Production ETL**
   ```sql
   CREATE WAREHOUSE prod_etl_multi_wh WITH
     WAREHOUSE_SIZE = 'LARGE'
     MIN_CLUSTER_COUNT = 2
     MAX_CLUSTER_COUNT = 4
     SCALING_POLICY = 'STANDARD'
     AUTO_SUSPEND = 600
     AUTO_RESUME = true;
   ```

3. **User-Facing Analytics**
   ```sql
   CREATE WAREHOUSE analytics_multi_wh WITH
     WAREHOUSE_SIZE = 'MEDIUM'
     MIN_CLUSTER_COUNT = 1
     MAX_CLUSTER_COUNT = 6
     SCALING_POLICY = 'STANDARD'
     AUTO_SUSPEND = 300
     AUTO_RESUME = true;
   ```

## 3. Auto-Suspend and Auto-Resume

### Auto-Suspend Best Practices

1. **Development Warehouses**
   ```sql
   ALTER WAREHOUSE dev_wh SET
     AUTO_SUSPEND = 300  -- 5 minutes
     AUTO_RESUME = true;
   ```

2. **ETL Warehouses**
   ```sql
   ALTER WAREHOUSE etl_wh SET
     AUTO_SUSPEND = 600  -- 10 minutes
     AUTO_RESUME = true;
   ```

3. **Analytics Warehouses**
   ```sql
   ALTER WAREHOUSE analytics_wh SET
     AUTO_SUSPEND = 900  -- 15 minutes
     AUTO_RESUME = true;
   ```

### Monitoring Suspension Patterns

```sql
-- Monitor warehouse suspension patterns
SELECT 
    warehouse_name,
    date_trunc('hour', start_time) as hour,
    COUNT(*) as suspend_count,
    AVG(credits_used) as avg_credits_before_suspend
FROM TABLE(information_schema.warehouse_metering_history(
    dateadd('days', -7, current_date()),
    current_date()))
WHERE end_time IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;
```

## 4. Cost vs Performance Trade-offs

### Size vs Clusters Trade-off Examples

1. **High Concurrency, Smaller Queries**

```sql
-- Better: More clusters, smaller size
CREATE WAREHOUSE concurrent_wh WITH
  WAREHOUSE_SIZE = 'SMALL'
  MIN_CLUSTER_COUNT = 2
  MAX_CLUSTER_COUNT = 6
  AUTO_SUSPEND = 300
  AUTO_RESUME = true;
```

2. **Low Concurrency, Complex Queries**

```sql
-- Better: Fewer clusters, larger size
CREATE WAREHOUSE complex_wh WITH
  WAREHOUSE_SIZE = 'XLARGE'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 2
  AUTO_SUSPEND = 600
  AUTO_RESUME = true;
```

### Monitoring and Optimization

```sql
-- Monitor warehouse utilization
CREATE OR REPLACE VIEW v_warehouse_utilization AS
SELECT 
    warehouse_name,
    date_trunc('day', start_time) as usage_date,
    COUNT(DISTINCT query_id) as query_count,
    SUM(credits_used) as total_credits,
    AVG(execution_time)/1000 as avg_execution_seconds,
    MAX(cluster_number) as max_clusters_used
FROM TABLE(information_schema.warehouse_metering_history(
    dateadd('days', -30, current_date()),
    current_date()))
GROUP BY 1, 2
ORDER BY 1, 2;
```

> AUTO_SUSPEND=300 means the warehouse will automatically suspend (shut down) after 300 seconds (5 minutes) of
> inactivity. This is a key cost-saving feature in Snowflake.