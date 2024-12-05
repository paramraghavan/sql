# Create, Delete, Insert vs LEFT ANTI JOIN Vs MErge

LEFT ANTI JOIN  is best because of :
## Performance Benefits:
* Single table scan of each table
* One-time write operation
* No intermediate results to manage
* Combines all logic into one step
* Can leverage clustering immediately


## Data Volume Considerations:
* With large history at 10GB, latest at 160GB, and small searchable_table
* LEFT ANTI JOIN can be optimized by Snowflake's query optimizer better than NOT EXISTS
* INNER JOIN with searchable_table eliminates the need for a separate DELETE

**Data Volume Context:**
```sql
large_history: 10GB
latest: 160GB 
searchable_table: small size
```

**LEFT ANTI JOIN Optimization:**
- A LEFT ANTI JOIN returns records from the left table that DON'T have matching records in the right table
- When comparing with `NOT EXISTS`, LEFT ANTI JOIN often performs better because:
    - Snowflake's optimizer can push predicates down more effectively
    - It can better utilize clustering and pruning optimizations
    - The engine can parallelize the operation more efficiently

**Example of LEFT ANTI JOIN vs NOT EXISTS:**
```sql
-- LEFT ANTI JOIN (Generally more efficient)
SELECT a.* 
FROM large_table a
LEFT ANTI JOIN lookup_table b ON a.id = b.id

-- NOT EXISTS (Less efficient)
SELECT a.*
FROM large_table a
WHERE NOT EXISTS (
    SELECT 1 
    FROM lookup_table b 
    WHERE a.id = b.id
)
```

**INNER JOIN Optimization:**

- When you need to both filter and delete records, using an INNER JOIN with your searchable criteria can be more
  efficient than:
    1. First finding the records to delete with a separate SELECT
    2. Then running a DELETE statement

- Example:
```sql
-- More efficient: Single operation with INNER JOIN
DELETE FROM large_table 
USING searchable_table
WHERE large_table.id = searchable_table.id;

-- Less efficient: Two separate operations
DELETE FROM large_table 
WHERE id IN (SELECT id FROM searchable_table);
```

The key insight here is that with such disparate table sizes (10GB, 160GB, and a small table), choosing the right join
strategy can significantly impact performance. Snowflake's optimizer works particularly well with LEFT ANTI JOIN
patterns when dealing with these size differences.


## MERGE would be better if:
* You needed to update existing records
* You were doing incremental loads
* You needed to handle duplicates



```sql
-- history and latest are very large tables and searchable_table is a small table
-- You can check clustering depth with
SELECT SYSTEM$CLUSTERING_DEPTH('history');

-- Monitor clustering information
SELECT SYSTEM$CLUSTERING_INFORMATION('history');

-- If needed, you can manually reclustering
ALTER TABLE history RECLUSTER;

ALTER TABLE history CLUSTER BY (search_id, search_dt);
ALTER TABLE latest CLUSTER BY (search_id, search_dt);

CREATE TABLE temp_table 
-- if these cols are used for updates
CLUSTER BY(search_id, search_dt) 
AS
SELECT a.search_id, a.search_dt, a.last_updt
FROM history a
LEFT ANTI JOIN latest b
    ON a.search_id = b.search_id 
    AND a.search_dt = b.search_dt
INNER JOIN searchable_table s 
    ON a.search_id = s.search_id;
    


CREATE TABLE temp_table AS
SELECT a.search_id, a.search_dt, a.last_updt,  -999 as col1, -999 as col2 
FROM history a
LEFT ANTI JOIN latest b
    ON a.search_id = b.search_id 
    AND a.search_dt = b.search_dt
INNER JOIN searchable_table s 
    ON a.search_id = s.search_id;
    
    
create table temp_table as 
select  
search_id, 
search_dt,
 -999 as col1,
 -999 as col2 
 from history;    
 
 
 -- split the temp_table into multiple temp table
 -- run udpates in separate thread and warehouse per temp_table
 -- join these table back into original table.
 
 
```

## Snowflake Insert Overwrite vs Insert Into

**INSERT OVERWRITE:**

When you execute:

```sql
INSERT OVERWRITE INTO mytable 
SELECT * FROM xyz;
```

This operation will delete/remove ALL existing rows in `mytable` and replace them with the results from the SELECT
query. _It's essentially equivalent to:_

```sql
TRUNCATE TABLE mytable;
INSERT INTO mytable 
SELECT * FROM xyz;
```
This is different from a regular `INSERT INTO` which would append the new rows to the existing data. Some key points to
understand:

1. The overwrite happens atomically - either the entire operation succeeds or fails
2. There's no way to recover the previous data unless you have Time Travel enabled
3. Any dependent objects (like materialized views) will be impacted


**INSERT INTO**

If you want to preserve existing data while adding new rows, use regular `INSERT INTO` instead:

```sql
INSERT INTO mytable 
SELECT * FROM xyz;
```

## MERGE - Update existing rows in `mytable` with matching rows from

`xyz` while keeping non-matching rows and inserting new rows,

You can use the MERGE statement. See below

```sql
MERGE INTO mytable t
USING xyz s
ON t.id = s.id  -- replace with your actual join key
WHEN MATCHED THEN 
    UPDATE SET 
        column1 = s.column1,
        column2 = s.column2
        -- list all columns you want to update
WHEN NOT MATCHED THEN
    INSERT (column1, column2, ...)  -- list all columns
    VALUES (s.column1, s.column2, ...);
```

This MERGE operation will:

1. Update existing rows in `mytable` when there's a matching `id` in `xyz`
2. Insert new rows from `xyz` when no matching `id` exists in `mytable`
3. Leave unchanged any rows in `mytable` that don't have matching records in `xyz`

For example, if your tables look like:

```sql
mytable:             xyz:
id  name  value     id  name  value
1   A     100       1   A     200    -- will update
2   B     150       3   C     300    -- will insert
4   D     400       -- this row stays unchanged
```

After the MERGE, `mytable` would contain:

```sql
id  name  value
1   A     200    -- updated
2   B     150    -- unchanged
3   C     300    -- inserted
4   D     400    -- unchanged
```

## Replace the entire column to updated

Yes, you can update all columns in the matched rows during a MERGE. Instead of listing each column individually, you can
use _"UPDATE SET *"_ to replace all columns:

```sql
MERGE INTO mytable t
USING xyz s
ON t.id = s.id  -- your join key
WHEN MATCHED THEN 
    UPDATE SET * -- replaces ALL columns with values from xyz
WHEN NOT MATCHED THEN
    INSERT (*) 
    VALUES (s.*);
```
Above :
1. Updates all columns from matching rows in `mytable` with values from `xyz`
2. Inserts new rows from `xyz` that don't exist in `mytable`
3. Preserves rows in `mytable` that don't have matches in `xyz`

