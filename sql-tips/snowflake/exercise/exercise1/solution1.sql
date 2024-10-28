-- Step 1: Create temporary tables with partitioned data
CREATE OR REPLACE TEMPORARY TABLE temp_table1 AS
SELECT *
FROM history
WHERE effective_date > '2023-10-01'
AND MOD(HASH(id), 4) = 0;  -- Adjust 'id' to your actual unique key column

CREATE OR REPLACE TEMPORARY TABLE temp_table2 AS
SELECT *
FROM history
WHERE effective_date > '2023-10-01'
AND MOD(HASH(id), 4) = 1;

CREATE OR REPLACE TEMPORARY TABLE temp_table3 AS
SELECT *
FROM history
WHERE effective_date > '2023-10-01'
AND MOD(HASH(id), 4) = 2;

CREATE OR REPLACE TEMPORARY TABLE temp_table4 AS
SELECT *
FROM history
WHERE effective_date > '2023-10-01'
AND MOD(HASH(id), 4) = 3;

-- Step 2: Apply updates to each temp table
-- Example update for temp_table1 (repeat similar updates for temp_table2-4)
UPDATE temp_table1
SET column1 = new_value1,
    column2 = new_value2
WHERE condition1;

-- Step 3: Merge updated data back to history table
MERGE INTO history h
USING (
    SELECT * FROM temp_table1
    UNION ALL
    SELECT * FROM temp_table2
    UNION ALL
    SELECT * FROM temp_table3
    UNION ALL
    SELECT * FROM temp_table4
) t
ON h.id = t.id  -- Adjust join condition based on your primary key
WHEN MATCHED THEN
    UPDATE SET
        h.column1 = t.column1,
        h.column2 = t.column2,
        -- Add other columns as needed
        h.last_updated = CURRENT_TIMESTAMP();

-- Optional: Clean up temporary tables
DROP TABLE IF EXISTS temp_table1;
DROP TABLE IF EXISTS temp_table2;
DROP TABLE IF EXISTS temp_table3;
DROP TABLE IF EXISTS temp_table4;
