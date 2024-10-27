# Snowflake Lock Escalation Overview

## Lock Types
1. **Row-Level Locks**
   - Initially starts with row locks
   - Each UPDATE/DELETE operation acquires a lock on the affected row
   - Multiple transactions can update different rows simultaneously

2. **Table-Level Locks**
   - Acquired for DDL operations
   - Can be acquired for large DML operations (lock escalation)
   - Types:
     - S (Shared) - allows concurrent reads
     - X (Exclusive) - no concurrent access
     - IS (Intent Shared)
     - IX (Intent Exclusive)

## Lock Escalation Triggers

1. **Number of Rows**
   ```sql
   -- If updating large number of rows in single transaction
   UPDATE table 
   SET column = value 
   WHERE condition; -- Affects many rows
   -- May trigger escalation to table lock
   ```

2. **Transaction Size**
   ```sql
   -- Multiple statements in same transaction
   BEGIN;
   UPDATE table SET col1 = val1 WHERE condition1;
   UPDATE table SET col2 = val2 WHERE condition2;
   UPDATE table SET col3 = val3 WHERE condition3;
   COMMIT;
   -- May escalate to table lock if total rows exceed threshold
   ```

## Best Practices to Avoid Lock Escalation

1. **Batch Processing**
   ```sql
   -- Instead of single large update
   UPDATE table 
   SET column = value 
   WHERE id IN (SELECT id FROM table WHERE condition)
   LIMIT 10000;
   ```

2. **Partition-Based Updates**
   ```sql
   -- Using micro-partitions
   UPDATE table 
   SET column = value 
   WHERE date_col BETWEEN '2024-01-01' AND '2024-01-31'
   ```

3. **Transaction Management**
   ```sql
   -- Smaller transaction scope
   BEGIN;
   UPDATE table SET col1 = val1 WHERE id BETWEEN 1 AND 1000;
   COMMIT;
   
   BEGIN;
   UPDATE table SET col1 = val1 WHERE id BETWEEN 1001 AND 2000;
   COMMIT;
   ```

## Monitoring Lock Escalation

```sql
-- Check for lock contention
SELECT * 
FROM table(information_schema.lock_wait_history())
WHERE table_name = 'YOUR_TABLE'
ORDER BY start_time DESC;

-- Monitor running transactions
SELECT * 
FROM table(information_schema.transactions_history())
WHERE status = 'RUNNING'
AND table_name = 'YOUR_TABLE';
```

## Impact on Parallel Processing Strategies

1. **Row-Based Strategy**
   ```sql
   -- Less likely to trigger lock escalation
   UPDATE table 
   SET column = value 
   WHERE primary_key = specific_value;
   ```

2. **Partition-Based Strategy**
   ```sql
   -- Moderate risk of lock escalation
   UPDATE table 
   SET column = value 
   WHERE MOD(HASH(id), 4) = partition_number
   AND date_col = specific_date;
   ```

3. **Full Table Strategy**
   ```sql
   -- High risk of lock escalation
   UPDATE table 
   SET column = value 
   WHERE condition = true;
   ```

## Lock Mitigation Strategies

1. **Time-Based Partitioning**
```sql
-- Update by time windows
UPDATE table 
SET column = value 
WHERE timestamp_col >= :start_time 
AND timestamp_col < :end_time;
```

2. **ID Range Partitioning**
```sql
-- Update by ID ranges
UPDATE table 
SET column = value 
WHERE id >= :start_id 
AND id < :end_id;
```

3. **Hybrid Approach**
```sql
-- Combine multiple partition strategies
UPDATE table 
SET column = value 
WHERE MOD(HASH(id), :num_partitions) = :partition_id
AND date_col = :specific_date
LIMIT :batch_size;
```

### Batching
```sql
-- Process in smaller chunks
UPDATE table 
SET status = 'PROCESSED'
WHERE id IN (SELECT id FROM table WHERE status = 'PENDING' LIMIT 1000);
```

### Use MERGE for Better Concurrency:
```sql
MERGE INTO target t
USING source s
ON t.id = s.id
WHEN MATCHED THEN UPDATE...
```

## When can row-level updates can potentially escalate to table locks under certain conditions. 

Here are the key scenarios:
**Lock Escalation Triggers:**
* When too many row locks are acquired (exceeding internal threshold)
* When a large percentage of table rows are being updated
* During concurrent updates to same set of rows
* When indexes are being updated extensively

**Common Situations Leading to Lock Escalation:**
```sql
-- Scenario 1: Mass updates affecting many rows
UPDATE large_table 
SET status = 'PROCESSED' 
WHERE create_date < CURRENT_DATE;

-- Scenario 2: Updates affecting indexed columns
UPDATE large_table 
SET indexed_column = new_value 
WHERE condition = true;

-- Scenario 3: Updates with complex WHERE clauses using multiple indexes
UPDATE large_table 
SET col1 = value 
WHERE index1 = 'x' AND index2 = 'y' AND index3 = 'z';
```

## Detect lock escalation on a table 

Snowflake, there isn't a direct way to view the exact internal threshold for lock escalation, but there are several ways
to monitor and identify lock-related issues:
```sql
-- Check current locks
SELECT * FROM TABLE(INFORMATION_SCHEMA.LOCK_STATES())
WHERE TABLE_NAME = 'YOUR_TABLE'
ORDER BY START_TIME DESC;

-- Check lock wait events
SELECT * FROM TABLE(INFORMATION_SCHEMA.LOGIN_HISTORY_TABLE())
WHERE ERROR_MESSAGE LIKE '%lock%'
ORDER BY EVENT_TIMESTAMP DESC;

-- Monitor sessions with locks
SELECT 
    SESSION_ID,
    USER_NAME,
    WAREHOUSE_NAME,
    QUERY_TEXT,
    EXECUTION_STATUS,
    ERROR_MESSAGE,
    START_TIME,
    END_TIME
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE QUERY_TEXT LIKE '%UPDATE%'
AND ERROR_MESSAGE LIKE '%lock%'
ORDER BY START_TIME DESC;
```



## Q and A
**Question:**
Let say snowflake table has 100 rows which can by identified uniquely, assuming we have the all the resources and the
same row is never updated in parallel, can we update each of the 100 rows in parallel at the same time without getting a
lock on the table

**Answer**
Yes, you can update all 100 rows in parallel if each row is uniquely identifiable and no two threads update the same row. 