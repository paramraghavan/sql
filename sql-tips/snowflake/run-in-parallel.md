# How  to perform multiple updates to the same table in parallel

Here's how you can handle parallel updates while minimizing table locks:

```sql
-- Method 1: Using MERGE statements with non-overlapping conditions
-- This allows parallel processing since each MERGE targets different rows

MERGE INTO target_table t
USING (SELECT col1, col2 FROM source_table WHERE condition1) s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.column1 = s.col1;

MERGE INTO target_table t
USING (SELECT col3, col4 FROM source_table WHERE condition2) s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.column2 = s.col3;

-- Method 2: Using separate transactions with BEGIN and COMMIT
-- Each transaction operates independently

BEGIN TRANSACTION;
UPDATE target_table 
SET column3 = new_value3 
WHERE condition3;
COMMIT;

BEGIN TRANSACTION;
UPDATE target_table 
SET column4 = new_value4 
WHERE condition4;
COMMIT;

-- Method 3: Using Snowflake Tasks for automated parallel execution
CREATE OR REPLACE TASK update_task_1
WAREHOUSE = compute_wh
SCHEDULE = '1 minute'
AS 
UPDATE target_table SET column5 = new_value5 WHERE condition5;

CREATE OR REPLACE TASK update_task_2
WAREHOUSE = compute_wh
SCHEDULE = '1 minute'
AS 
UPDATE target_table SET column6 = new_value6 WHERE condition6;

ALTER TASK update_task_1 RESUME;
ALTER TASK update_task_2 RESUME;

-- Method 4: Using separate virtual warehouses
-- First, create dedicated warehouses
CREATE WAREHOUSE IF NOT EXISTS wh_updates_1 
WITH WAREHOUSE_SIZE = 'XSMALL' --MEDIUM, LARGE
AUTO_SUSPEND = 60 
AUTO_RESUME = TRUE;

CREATE WAREHOUSE IF NOT EXISTS wh_updates_2
WITH WAREHOUSE_SIZE = 'XSMALL' 
AUTO_SUSPEND = 60 
AUTO_RESUME = TRUE;

-- Then use USE WAREHOUSE in separate sessions
USE WAREHOUSE wh_updates_1;
UPDATE target_table SET column7 = new_value7 WHERE condition7;

-- In another session
USE WAREHOUSE wh_updates_2;
UPDATE target_table SET column8 = new_value8 WHERE condition8;

```

Here are the key strategies to run multiple updates in parallel while maintaining table availability:

1. Use MERGE statements instead of UPDATE:
    - MERGE provides better concurrency control
    - Each MERGE can target different columns independently
    - Less likely to cause table-level locks

2. Separate transactions:
    - Break updates into individual transactions
    - Each transaction can run independently
    - Shorter transaction duration means less blocking

3. Snowflake Tasks:
    - Create separate tasks for each update
    - Tasks can run in parallel automatically
    - Provides built-in scheduling and monitoring

4. Multiple virtual warehouses:
    - Use separate warehouses for different updates
    - Enables true parallel processing
    - Better resource isolation

Best practices:

- Ensure updates target different rows when possible
- Keep transactions short
- Use appropriate warehouse sizes
- Monitor for conflicts using SYSTEM$LOCK_WAIT_HISTORY

# Another idea split the table in N parts and combine together after the updates

Here are effective methods to split a large table into 4-5 temporary tables with balanced distribution:

```sql
-- Method 1: Using ROW_NUMBER() for even distribution
CREATE OR REPLACE TEMPORARY TABLE temp_table_1 AS
WITH numbered_rows AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY id) AS rn
    FROM main_table
)
SELECT * FROM numbered_rows 
WHERE MOD(rn, 4) = 0;

CREATE OR REPLACE TEMPORARY TABLE temp_table_2 AS
WITH numbered_rows AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY id) AS rn
    FROM main_table
)
SELECT * FROM numbered_rows 
WHERE MOD(rn, 4) = 1;

-- Table 1: Gets rows 4, 8, 12, 16...
WHERE MOD(rn, 4) = 0  
-- Table 2: Gets rows 1, 5, 9, 13...
WHERE MOD(rn, 4) = 1  
-- Table 3: Gets rows 2, 6, 10, 14...
WHERE MOD(rn, 4) = 2  
-- Table 4: Gets rows 3, 7, 11, 15...
WHERE MOD(rn, 4) = 3

-- Method 2: Using NTILE for percentage-based splitting
CREATE OR REPLACE TEMPORARY TABLE temp_table_1 AS
SELECT * FROM (
    SELECT *,
           NTILE(4) OVER (ORDER BY id) AS bucket
    FROM main_table
)
WHERE bucket = 1;

CREATE OR REPLACE TEMPORARY TABLE temp_table_2 AS
SELECT * FROM (
    SELECT *,
           NTILE(4) OVER (ORDER BY id) AS bucket
    FROM main_table
)
WHERE bucket = 2;

-- Method 3: Using value ranges (if ID is sequential and evenly distributed)
-- First, find the range
WITH boundaries AS (
    SELECT 
        MIN(id) as min_id,
        MAX(id) as max_id,
        CEIL((MAX(id) - MIN(id))/4) as range_size
    FROM main_table
)
SELECT * FROM boundaries;

-- Then split based on ranges
CREATE OR REPLACE TEMPORARY TABLE temp_table_1 AS
SELECT * FROM main_table
WHERE id BETWEEN (SELECT min_id FROM boundaries)
                 AND (SELECT min_id + range_size FROM boundaries);

CREATE OR REPLACE TEMPORARY TABLE temp_table_2 AS
SELECT * FROM main_table
WHERE id BETWEEN (SELECT min_id + range_size + 1 FROM boundaries)
                 AND (SELECT min_id + (range_size * 2) FROM boundaries);

-- Method 4: Using HASH for random but even distribution
CREATE OR REPLACE TEMPORARY TABLE temp_table_1 AS
SELECT * FROM main_table
WHERE MOD(ABS(HASH(id)), 4) = 0;

CREATE OR REPLACE TEMPORARY TABLE temp_table_2 AS
SELECT * FROM main_table
WHERE MOD(ABS(HASH(id)), 4) = 1;

-- Verification Query to check distribution
SELECT 
    'temp_table_1' as table_name, COUNT(*) as row_count 
FROM temp_table_1
UNION ALL
SELECT 
    'temp_table_2', COUNT(*) 
FROM temp_table_2
UNION ALL
SELECT 
    'temp_table_3', COUNT(*) 
FROM temp_table_3
UNION ALL
SELECT 
    'temp_table_4', COUNT(*) 
FROM temp_table_4
ORDER BY table_name;

```

Here's why each method might be useful:

1. **ROW_NUMBER Method**
    - Pros:
        - Perfectly even distribution
        - Sequential splitting
    - Best for: When you need exact equal sizes
    - Use when: Order doesn't matter

2. **NTILE Method**
    - Pros:
        - Automatically handles uneven divisions
        - Maintains relative ordering
    - Best for: When you need percentage-based splits
    - Use when: You want similar-sized chunks

3. **Range-Based Method**
    - Pros:
        - Simple to understand and debug
        - Maintains data locality
    - Best for: Sequential IDs
    - Use when: ID values are evenly distributed

4. **HASH Method**
    - Pros:
        - Random but deterministic distribution
        - Works well with any ID type
    - Best for: Non-sequential IDs
    - Use when: You want random but repeatable splits

To choose the best method:
1. If IDs are sequential and evenly distributed: Use Range-Based
2. If exact equal sizes are needed: Use ROW_NUMBER
3. If random distribution is acceptable: Use HASH
4. If percentage-based splitting is needed: Use NTILE

