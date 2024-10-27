# Multi-warehouse parallel update


1. **Using Different Warehouses for Different Workloads:**
```python
# For heavy updates
heavy_update = {
    'sql': "UPDATE your_table SET heavy_column = complex_calculation()",
    'warehouses': ['WAREHOUSE_XLARGE_1', 'WAREHOUSE_XLARGE_2']
}

# For light updates
light_update = {
    'sql': "UPDATE your_table SET status = 'COMPLETE'",
    'warehouses': ['WAREHOUSE_SMALL_1', 'WAREHOUSE_SMALL_2', 'WAREHOUSE_SMALL_3', 'WAREHOUSE_SMALL_4']
}

# Execute updates
for update in [heavy_update, light_update]:
    results = updater.parallel_update(
        update_sql=update['sql'],
        num_partitions=len(update['warehouses']),
        warehouses=update['warehouses']
    )
```

2. **Dynamic Warehouse Allocation:**
```python
# Based on data volume
def get_warehouses(row_count):
    if row_count > 1000000:
        return ['WH_XLARGE_1', 'WH_XLARGE_2']
    elif row_count > 100000:
        return ['WH_LARGE_1', 'WH_LARGE_2', 'WH_LARGE_3']
    else:
        return 'WH_MEDIUM'  # Single warehouse for smaller updates

# Get row count
cursor.execute("SELECT COUNT(*) FROM your_table WHERE condition = true")
row_count = cursor.fetchone()[0]

# Execute update with appropriate warehouses
results = updater.parallel_update(
    update_sql=update_sql,
    num_partitions=2 if row_count > 1000000 else 3,
    warehouses=get_warehouses(row_count)
)
```

3. **With Warehouse Management:**
```python
def setup_warehouse(name, size):
    cursor.execute(f"""
        CREATE WAREHOUSE IF NOT EXISTS {name}
        WITH WAREHOUSE_SIZE = '{size}'
        AUTO_SUSPEND = 60
        AUTO_RESUME = TRUE
    """)

# Setup warehouses before updates
warehouses = ['WH_1', 'WH_2', 'WH_3', 'WH_4']
for wh in warehouses:
    setup_warehouse(wh, 'LARGE')
```