# Types of Locks:

## Row-Level Locks:
* Primary lock mechanism
* Only locks specific rows being modified
* Other rows remain accessible


## Table-Level Locks:
* Used for DDL operations (ALTER TABLE, etc.)
* Metadata operations
* Schema changes

## Lock Duration:
* Locks are held for the duration of the transaction
* Auto-commit if not in explicit transaction
* Released when transaction commits/rollbacks


## These operations acquire locks:
```sql
UPDATE, DELETE, MERGE
INSERT (only for duplicate key checks)
SELECT ... FOR UPDATE
```

## Avoid Lock Contention:
### Keep Transactions Short:
```sql
-- Good
BEGIN;
UPDATE table SET status = 'DONE' WHERE batch_id = 123;
COMMIT;

-- Avoid long-running transactions
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
