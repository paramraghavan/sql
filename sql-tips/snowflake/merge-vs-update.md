Let me explain how MERGE works and its key differences from UPDATE with examples.

```sql
-- Let's create sample tables to demonstrate
CREATE TABLE target_customers (
    customer_id INT,
    name STRING,
    email STRING,
    status STRING,
    last_updated TIMESTAMP
);

CREATE TABLE source_updates (
    customer_id INT,
    new_email STRING,
    new_status STRING,
    update_timestamp TIMESTAMP
);

-- 1. Basic UPDATE approach
-- Requires multiple scans and separate operations
UPDATE target_customers t
SET email = s.new_email,
    status = s.new_status,
    last_updated = s.update_timestamp
FROM source_updates s
WHERE t.customer_id = s.customer_id;

-- 2. MERGE equivalent - Single atomic operation
MERGE INTO target_customers t
USING source_updates s
    ON t.customer_id = s.customer_id  -- Match condition
WHEN MATCHED THEN 
    UPDATE SET 
        t.email = s.new_email,
        t.status = s.new_status,
        t.last_updated = s.update_timestamp;

-- 3. MERGE with complex logic and conditions
MERGE INTO target_customers t
USING (
    SELECT 
        customer_id,
        new_email,
        new_status,
        update_timestamp,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY update_timestamp DESC) as rn
    FROM source_updates
    QUALIFY rn = 1  -- Takes only the latest update for each customer
) s
ON t.customer_id = s.customer_id
WHEN MATCHED 
    AND s.new_status IS NOT NULL 
    AND t.status != s.new_status 
THEN UPDATE SET 
    t.email = COALESCE(s.new_email, t.email),
    t.status = s.new_status,
    t.last_updated = s.update_timestamp
WHEN NOT MATCHED BY TARGET 
    AND s.new_status = 'NEW' 
THEN INSERT (
    customer_id, 
    email, 
    status, 
    last_updated
) VALUES (
    s.customer_id,
    s.new_email,
    s.new_status,
    s.update_timestamp
);

-- 4. Monitoring MERGE vs UPDATE execution
-- You can see the difference in query plans
EXPLAIN USING TEXT
MERGE INTO target_customers t
USING source_updates s
ON t.customer_id = s.customer_id
WHEN MATCHED THEN UPDATE SET 
    t.email = s.new_email;

EXPLAIN USING TEXT
UPDATE target_customers t
SET email = s.new_email
FROM source_updates s
WHERE t.customer_id = s.customer_id;

-- 5. Example of MERGE with multiple source tables
MERGE INTO target_customers t
USING (
    -- Complex source query combining multiple tables
    SELECT 
        c.customer_id,
        c.email as new_email,
        CASE 
            WHEN o.total_orders > 100 THEN 'PLATINUM'
            WHEN o.total_orders > 50 THEN 'GOLD'
            ELSE 'REGULAR'
        END as new_status,
        CURRENT_TIMESTAMP() as update_timestamp
    FROM customer_updates c
    JOIN (
        SELECT customer_id, COUNT(*) as total_orders
        FROM orders
        GROUP BY customer_id
    ) o ON c.customer_id = o.customer_id
) s
ON t.customer_id = s.customer_id
WHEN MATCHED THEN UPDATE SET 
    t.email = s.new_email,
    t.status = s.new_status,
    t.last_updated = s.update_timestamp;

```

Here's how MERGE works differently from UPDATE:

1. **Operation Flow:**

   **UPDATE Process:**
   ```
   1. Scans target table
   2. For each row, checks WHERE condition
   3. If condition met, acquires row lock
   4. Updates the row
   5. Moves to next row
   ```

   **MERGE Process:**
   ```
   1. Creates a merge plan combining source and target
   2. Identifies all matching rows in one pass
   3. Determines required actions (UPDATE/INSERT/DELETE)
   4. Executes all actions in a single atomic operation
   5. Manages locks more efficiently
   ```

2. **Key Differences:**

   a. **Data Processing:**
    - UPDATE: Processes row by row
    - MERGE: Set-based operation, processes all matches at once

   b. **Lock Management:**
    - UPDATE: Acquires locks as it processes each row
    - MERGE: Optimizes lock acquisition for the entire operation

   c. **Performance:**
    - UPDATE: Multiple table scans for complex operations
    - MERGE: Single pass through the data

3. **MERGE Advantages:**

   a. **Atomic Operations:**
   ```sql
   -- MERGE handles multiple operations atomically
   MERGE INTO target t
   USING source s
   ON t.id = s.id
   WHEN MATCHED THEN UPDATE...
   WHEN NOT MATCHED THEN INSERT...
   ```

   b. **Complex Conditions:**
   ```sql
   MERGE INTO target t
   USING source s
   ON t.id = s.id
   WHEN MATCHED AND s.status = 'ACTIVE' THEN UPDATE...
   WHEN MATCHED AND s.status = 'INACTIVE' THEN DELETE...
   ```

4. **Use Cases Where MERGE is Better:**

    - Upsert operations (UPDATE + INSERT)
    - Complex data synchronization
    - Data warehouse loads
    - Multi-table updates
    - High-concurrency environments

5. **Memory and Resource Usage:**
    - MERGE typically uses memory more efficiently
    - Better optimization of concurrent operations
    - More efficient execution plans

6. **Best Practices:**

   a. **Use MERGE when:**
   ```sql
   - Multiple DML operations needed
   - Complex source data joining
   - Need atomic operations
   - High concurrency requirements
   ```

   b. **Stick with UPDATE when:**
   ```sql
   - Simple single-table updates
   - No need for INSERT/DELETE
   - Simple WHERE conditions
   ```
