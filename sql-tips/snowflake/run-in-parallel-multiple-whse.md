# How to use multiple virtual warehouses to run parallel updates effectively.

```sql
-- 1. First create separate warehouses for parallel processing
CREATE WAREHOUSE IF NOT EXISTS WH_UPDATE_1
WITH WAREHOUSE_SIZE = 'MEDIUM'
AUTO_SUSPEND = 300
AUTO_RESUME = TRUE
INITIALLY_SUSPENDED = TRUE;

CREATE WAREHOUSE IF NOT EXISTS WH_UPDATE_2
WITH WAREHOUSE_SIZE = 'MEDIUM'
AUTO_SUSPEND = 300
AUTO_RESUME = TRUE
INITIALLY_SUSPENDED = TRUE;

CREATE WAREHOUSE IF NOT EXISTS WH_UPDATE_3
WITH WAREHOUSE_SIZE = 'MEDIUM'
AUTO_SUSPEND = 300
AUTO_RESUME = TRUE
INITIALLY_SUSPENDED = TRUE;

-- 2. Example table setup (if you need to test)
CREATE OR REPLACE TABLE customer_data (
    id NUMBER,
    first_name STRING,
    last_name STRING,
    email STRING,
    address STRING,
    credit_score NUMBER,
    last_purchase_date DATE,
    total_purchases NUMBER
);

-- 3. Now run these updates in separate sessions/worksheets

-- SESSION 1: Using First Warehouse
USE WAREHOUSE WH_UPDATE_1;
UPDATE customer_data 
SET credit_score = credit_score + 10,
    last_purchase_date = CURRENT_DATE()
WHERE id BETWEEN 1 AND 10000;

-- SESSION 2: Using Second Warehouse
USE WAREHOUSE WH_UPDATE_2;
UPDATE customer_data 
SET total_purchases = total_purchases + 1,
    address = 'New Address'
WHERE id BETWEEN 10001 AND 20000;

-- SESSION 3: Using Third Warehouse
USE WAREHOUSE WH_UPDATE_3;
UPDATE customer_data 
SET first_name = 'Updated',
    email = 'new@email.com'
WHERE id BETWEEN 20001 AND 30000;

-- 4. Monitor running queries (run in a separate session)
SELECT 
    query_id,
    query_text,
    user_name,
    warehouse_name,
    execution_status,
    error_message,
    start_time,
    end_time,
    total_elapsed_time/1000 as seconds_taken
FROM table(information_schema.query_history())
WHERE query_type = 'UPDATE'
AND start_time >= DATEADD(hours, -1, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- 5. Monitor warehouse resource usage
SELECT
    warehouse_name,
    COUNT(*) as query_count,
    AVG(total_elapsed_time)/1000 as avg_seconds,
    MAX(total_elapsed_time)/1000 as max_seconds
FROM table(information_schema.query_history())
WHERE query_type = 'UPDATE'
AND start_time >= DATEADD(hours, -1, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY query_count DESC;

-- 6. Suspend warehouses after use (optional)
ALTER WAREHOUSE WH_UPDATE_1 SUSPEND;
ALTER WAREHOUSE WH_UPDATE_2 SUSPEND;
ALTER WAREHOUSE WH_UPDATE_3 SUSPEND;

```

Here's how to implement this in practice:

1. **Set Up Warehouses:**
   ```sql
   -- Create dedicated warehouses for each update stream
   CREATE WAREHOUSE WH_UPDATE_1 WITH WAREHOUSE_SIZE = 'MEDIUM'...
   ```
    - Choose appropriate warehouse sizes based on workload
    - Enable AUTO_SUSPEND to save credits
    - Enable AUTO_RESUME for convenience

2. **Execute Updates:**
    - Open multiple worksheets/sessions in Snowflake
    - In each session, first set the warehouse:
   ```sql
   USE WAREHOUSE WH_UPDATE_1;
   -- Then run your update
   UPDATE table SET column1 = value WHERE condition;
   ```

3. **Real-World Example:**

```sql
-- Session 1 (Worksheet 1)
USE WAREHOUSE WH_UPDATE_1;
UPDATE customer_data 
SET credit_score = credit_score + 10
WHERE id < 10000;

-- Session 2 (Worksheet 2)
USE WAREHOUSE WH_UPDATE_2;
UPDATE customer_data 
SET email = 'new@email.com'
WHERE id BETWEEN 10001 AND 20000;

-- Session 3 (Worksheet 3)
USE WAREHOUSE WH_UPDATE_3;
UPDATE customer_data 
SET address = 'New Address'
WHERE id > 20000;
```

4. **Best Practices:**
    - Split updates by non-overlapping WHERE conditions
    - Use appropriate warehouse sizes
    - Monitor query performance using query history
    - Suspend warehouses when done
    - Consider cost implications of multiple warehouses

5. **Monitoring Tips:**
    - Use the query history view to track progress
    - Monitor warehouse utilization
    - Check for any conflicts or deadlocks

6. **Cost Considerations:**
    - Each warehouse consumes separate credits
    - Size warehouses appropriately
    - Use AUTO_SUSPEND to minimize costs
    - Monitor credit usage

## how does multiple warehouse prevent locks and allow parallel update as we are working with a single table across warehouse

How multiple warehouses work with table locking in Snowflake:

1. **Important to Note:**
    - Multiple warehouses alone DON'T prevent table locks
    - Snowflake uses row-level locking, not table-level locking
    - The key is HOW you structure your updates, not just using different warehouses

Here's how to effectively use multiple warehouses for parallel updates:

```sql
-- BAD PRACTICE: These will conflict even with different warehouses
-- Warehouse 1
USE WAREHOUSE WH_UPDATE_1;
UPDATE customer_table 
SET email = 'new@email.com' 
WHERE status = 'ACTIVE';  -- Overlapping rows with other updates

-- Warehouse 2
USE WAREHOUSE WH_UPDATE_2;
UPDATE customer_table 
SET phone = '123-456-7890' 
WHERE status = 'ACTIVE';  -- Same rows, will cause locks

-- GOOD PRACTICE: Non-overlapping row updates
-- Warehouse 1
USE WAREHOUSE WH_UPDATE_1;
UPDATE customer_table 
SET email = 'new@email.com',
    phone = '123-456-7890',
    address = 'New Address'
WHERE id BETWEEN 1 AND 10000;

-- Warehouse 2
USE WAREHOUSE WH_UPDATE_2;
UPDATE customer_table 
SET email = 'new@email.com',
    phone = '123-456-7890',
    address = 'New Address'
WHERE id BETWEEN 10001 AND 20000;

-- BETTER PRACTICE: Using micro-batching with non-overlapping rows
-- Warehouse 1
USE WAREHOUSE WH_UPDATE_1;
BEGIN TRANSACTION;
UPDATE customer_table 
SET email = 'new@email.com',
    phone = '123-456-7890'
WHERE id IN (
    SELECT id 
    FROM customer_table 
    WHERE id BETWEEN 1 AND 10000
    AND id NOT IN (SELECT id FROM updated_records)
    LIMIT 1000
);
COMMIT;

-- Monitor lock conflicts
SELECT * 
FROM TABLE(INFORMATION_SCHEMA.LOCK_CONFLICTS(
    SESSION_ID=>CURRENT_SESSION()
));

-- Check blocking queries
SELECT *
FROM TABLE(INFORMATION_SCHEMA.CURRENT_LOCKS());

-- Best Practice: Merge approach for better concurrency
-- Warehouse 1
USE WAREHOUSE WH_UPDATE_1;
MERGE INTO customer_table t
USING (
    SELECT id, 'new@email.com' as new_email, '123-456-7890' as new_phone
    FROM customer_table
    WHERE id BETWEEN 1 AND 10000
) s
ON t.id = s.id
WHEN MATCHED THEN UPDATE
SET t.email = s.new_email,
    t.phone = s.new_phone;

```

2. **Key Strategies for True Parallel Updates:**

   a. **Non-overlapping Data Partitions:**
   ```sql
   -- Warehouse 1
   UPDATE table WHERE id BETWEEN 1 AND 10000
   
   -- Warehouse 2
   UPDATE table WHERE id BETWEEN 10001 AND 20000
   ```

   b. **Micro-batching:**
   ```sql
   -- Process in smaller chunks to reduce lock duration
   UPDATE table 
   WHERE id IN (SELECT id FROM table WHERE condition LIMIT 1000)
   ```

   c. **MERGE Instead of UPDATE:**
   ```sql
   -- Better concurrency control
   MERGE INTO table USING (SELECT...) source ON conditions
   ```

3. **Why Multiple Warehouses Are Still Useful:**
    - Separate compute resources for each update stream
    - Better performance monitoring
    - Independent resource scaling
    - Easier cost tracking
    - Workload isolation

4. **Best Practices for Parallel Updates:**
    - Always use non-overlapping WHERE conditions
    - Consider using MERGE statements
    - Implement micro-batching for large updates
    - Monitor lock conflicts
    - Use appropriate transaction sizes
    - Consider time-based partitioning if relevant

5. **Common Issues to Avoid:**
   ```sql
   -- DON'T: Update same rows from different warehouses
   UPDATE table SET col1 = 'value' WHERE status = 'ACTIVE';  -- Warehouse 1
   UPDATE table SET col2 = 'value' WHERE status = 'ACTIVE';  -- Warehouse 2

   -- DO: Split rows between warehouses
   UPDATE table SET col1 = 'value', col2 = 'value' WHERE id < 5000;  -- Warehouse 1
   UPDATE table SET col1 = 'value', col2 = 'value' WHERE id >= 5000; -- Warehouse 2
   ```

6. **Monitoring Locks:**
   ```sql
   -- Check for lock conflicts
   SELECT * FROM TABLE(INFORMATION_SCHEMA.LOCK_CONFLICTS());
   
   -- Monitor blocking queries
   SELECT * FROM TABLE(INFORMATION_SCHEMA.CURRENT_LOCKS());
   ```