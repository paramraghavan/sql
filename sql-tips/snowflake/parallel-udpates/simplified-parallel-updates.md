# PArallel udpates

1. **Reusability:**
    - Single class that handles any type of UPDATE
    - Just pass your UPDATE SQL and number of partitions
    - No need to modify code for different updates

2. **Easy to Use:**
   ```python
   # Quick example
   updater = SimpleParallelUpdater(conn_params)
   
   # Run any update in parallel
   results = updater.parallel_update(
       "UPDATE your_table SET col1 = 'value' WHERE condition = true"
   )
   ```

3. **Minimal Setup:**
    - No temporary tables needed
    - No pre-computation required
    - Works directly on your table

4. **Flexible:**
    - Can handle any UPDATE statement
    - Easily adjust number of partitions
    - Works with any WHERE clause

Usage tips:

1. **For Very Large Updates:**

```python
# Use more partitions
results = updater.parallel_update(update_sql, num_partitions=8)
```

2. **For Complex Updates:**

```python
# Multi-condition updates
complex_update = """
    UPDATE your_table 
    SET 
        col1 = CASE 
            WHEN condition1 THEN 'value1'
            WHEN condition2 THEN 'value2'
            ELSE 'value3'
        END,
        col2 = expression2
    WHERE some_condition = true
"""
results = updater.parallel_update(complex_update)
```

3. **Error Handling:**

```python
results = updater.parallel_update(update_sql)
if any(r['status'] == 'error' for r in results):
    # Handle errors
    failed_partitions = [r for r in results if r['status'] == 'error']
    print(f"Failed partitions: {failed_partitions}")
```
