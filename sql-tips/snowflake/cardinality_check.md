# Cardinality Check

Higher number of unique values means higher cardinality!

High Cardinality Example:

```sql
-- Example: Customer ID column
SELECT 
    COUNT(DISTINCT customer_id) as unique_values,
    COUNT(*) as total_rows,
    (COUNT(DISTINCT customer_id) / COUNT(*)::float) * 100 as cardinality_percentage
FROM customers;

-- Result might look like:
-- unique_values: 900,000
-- total_rows: 1,000,000
-- cardinality_percentage: 90%  (High cardinality - good for clustering)
```

Low Cardinality Example:

```sql
-- Example: Status column
SELECT 
    COUNT(DISTINCT status) as unique_values,
    COUNT(*) as total_rows,
    (COUNT(DISTINCT status) / COUNT(*)::float) * 100 as cardinality_percentage
FROM customers;

-- Result might look like:
-- unique_values: 5 ('active', 'inactive', 'pending', 'suspended', 'closed')
-- total_rows: 1,000,000
-- cardinality_percentage: 0.0005%  (Low cardinality - poor for clustering)
```

Rule of Thumb:

- High Cardinality: > 20% unique values (Good for clustering)
- Medium Cardinality: 5-20% unique values (May be okay in combination)
- Low Cardinality: < 5% unique values (Poor for clustering alone)

Visual Example:

```
High Cardinality (Customer ID):
1001, 1002, 1003, 1004, 1005... (many unique values)
↓ Good for clustering

Low Cardinality (Status):
active, inactive, active, active, inactive... (few unique values repeating)
↓ Poor for clustering alone
```

Would you like me to help analyze the cardinality of specific columns in your table?