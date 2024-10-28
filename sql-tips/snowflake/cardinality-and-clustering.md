# clustering and cardinality in Snowflake in a comprehensive way.

```sql
-- 1. Demonstrate different cardinality levels
CREATE OR REPLACE TABLE cardinality_examples (
    -- Low cardinality columns
    status VARCHAR(10),           -- Few distinct values (e.g., 'active', 'inactive')
    country_code CHAR(2),         -- Limited distinct values (~200 countries)
    payment_type VARCHAR(20),     -- Few options (e.g., 'credit', 'debit', 'cash')
    
    -- Medium cardinality columns
    product_category VARCHAR(50), -- Moderate distinct values (hundreds)
    store_id NUMBER,             -- Moderate distinct values (thousands)
    
    -- High cardinality columns
    customer_id NUMBER,          -- Many distinct values (millions)
    transaction_id VARCHAR,      -- Unique per row
    email VARCHAR(255),          -- Almost unique per customer
    
    -- Date columns (varying cardinality based on grouping)
    transaction_date DATE,
    created_timestamp TIMESTAMP
);

-- 2. Analyze cardinality levels
WITH cardinality_analysis AS (
    SELECT 
        'Status' as column_name,
        COUNT(DISTINCT status) as distinct_values,
        COUNT(*) as total_rows,
        COUNT(DISTINCT status) / COUNT(*) * 100 as cardinality_ratio
    FROM cardinality_examples
    
    UNION ALL
    
    SELECT 
        'Country Code',
        COUNT(DISTINCT country_code),
        COUNT(*),
        COUNT(DISTINCT country_code) / COUNT(*) * 100
    FROM cardinality_examples
    
    UNION ALL
    
    SELECT 
        'Customer ID',
        COUNT(DISTINCT customer_id),
        COUNT(*),
        COUNT(DISTINCT customer_id) / COUNT(*) * 100
    FROM cardinality_examples
)
SELECT 
    column_name,
    distinct_values,
    total_rows,
    ROUND(cardinality_ratio, 2) as cardinality_percentage,
    CASE 
        WHEN cardinality_ratio < 1 THEN 'Very Low (Excellent for clustering)'
        WHEN cardinality_ratio < 5 THEN 'Low (Good for clustering)'
        WHEN cardinality_ratio < 20 THEN 'Medium (Consider as secondary)'
        ELSE 'High (Not recommended for clustering)'
    END as cardinality_assessment
FROM cardinality_analysis;

-- 3. Demonstrate good clustering examples
-- Example 1: Date-based clustering
CREATE OR REPLACE TABLE sales_data_good_clustering (
    transaction_date DATE,
    country_code CHAR(2),
    product_category VARCHAR(50),
    amount NUMBER,
    customer_id NUMBER
)
CLUSTER BY (
    DATE_TRUNC('MONTH', transaction_date), -- Low cardinality (12 values per year)
    country_code,                          -- Low cardinality (~200 values)
    product_category                       -- Medium cardinality
);

-- Example 2: Business logic clustering
CREATE OR REPLACE TABLE orders_good_clustering (
    order_status VARCHAR(10),
    order_type VARCHAR(20),
    region VARCHAR(50),
    amount NUMBER,
    customer_id NUMBER
)
CLUSTER BY (
    order_status,  -- Low cardinality (e.g., 'pending', 'completed', 'cancelled')
    order_type,    -- Low cardinality (e.g., 'retail', 'wholesale', 'online')
    region         -- Low cardinality (e.g., 'North', 'South', 'East', 'West')
);

-- 4. Demonstrate bad clustering examples
CREATE OR REPLACE TABLE bad_clustering_example (
    customer_id NUMBER,
    email VARCHAR(255),
    transaction_id VARCHAR,
    amount NUMBER
)
CLUSTER BY (
    customer_id,     -- High cardinality
    email,          -- High cardinality
    transaction_id  -- Unique per row (worst for clustering)
);

-- 5. Monitor clustering effectiveness
CREATE OR REPLACE PROCEDURE MONITOR_CLUSTERING_EFFECTIVENESS(
    TABLE_NAME STRING,
    CLUSTERING_KEYS ARRAY
)
RETURNS TABLE (
    metric_name VARCHAR,
    metric_value VARIANT,
    assessment VARCHAR
)
LANGUAGE JAVASCRIPT
AS
$$
    var metrics = [];
    var clustering_key_str = CLUSTERING_KEYS.join(', ');
    
    // Analyze clustering depth
    var depthQuery = `
        SELECT 
            'Clustering Depth' as metric_name,
            SYSTEM$CLUSTERING_DEPTH() as metric_value,
            CASE 
                WHEN SYSTEM$CLUSTERING_DEPTH() <= 3 THEN 'Excellent'
                WHEN SYSTEM$CLUSTERING_DEPTH() <= 5 THEN 'Good'
                WHEN SYSTEM$CLUSTERING_DEPTH() <= 7 THEN 'Fair'
                ELSE 'Poor'
            END as assessment
        FROM ${TABLE_NAME}
    `;
    
    // Analyze cardinality
    var cardinalityQuery = `
        SELECT 
            'Cardinality Ratio' as metric_name,
            COUNT(DISTINCT (${clustering_key_str})) / COUNT(*) * 100 as metric_value,
            CASE 
                WHEN COUNT(DISTINCT (${clustering_key_str})) / COUNT(*) * 100 < 1 THEN 'Excellent'
                WHEN COUNT(DISTINCT (${clustering_key_str})) / COUNT(*) * 100 < 5 THEN 'Good'
                WHEN COUNT(DISTINCT (${clustering_key_str})) / COUNT(*) * 100 < 20 THEN 'Fair'
                ELSE 'Poor'
            END as assessment
        FROM ${TABLE_NAME}
    `;
    
    // Execute queries and compile results
    var stmt1 = snowflake.createStatement({sqlText: depthQuery});
    var stmt2 = snowflake.createStatement({sqlText: cardinalityQuery});
    
    var rs1 = stmt1.execute();
    var rs2 = stmt2.execute();
    
    while (rs1.next()) {
        metrics.push([rs1.getColumnValue(1), rs1.getColumnValue(2), rs1.getColumnValue(3)]);
    }
    
    while (rs2.next()) {
        metrics.push([rs2.getColumnValue(1), rs2.getColumnValue(2), rs2.getColumnValue(3)]);
    }
    
    return metrics;
$$;

```

Key Concepts:

1. **Cardinality Types:**
    - **Low Cardinality** (< 1% unique values)
        - Status codes (active/inactive)
        - Country codes
        - Categories
    - **Medium Cardinality** (1-20% unique values)
        - Store IDs
        - Product categories
    - **High Cardinality** (> 20% unique values)
        - Customer IDs
        - Email addresses
        - Transaction IDs

2. **Clustering Best Practices:**
    - Start with lowest cardinality columns
    - Limit to 3-4 columns maximum
    - Order matters (most selective first)
    - Consider query patterns

3. **Why Cardinality Matters for Clustering:**
    - **Low Cardinality Benefits:**
        - Better data organization
        - Efficient micro-partition pruning
        - Faster query performance

    - **High Cardinality Problems:**
        - Many micro-partitions
        - Poor pruning efficiency
        - Higher maintenance overhead

4. **Real-World Examples:**
   ```sql
   -- Good clustering (low cardinality)
   CLUSTER BY (
       DATE_TRUNC('MONTH', date),
       region,
       category
   )
   
   -- Bad clustering (high cardinality)
   CLUSTER BY (
       customer_id,
       email,
       transaction_id
   )
   ```

5. **Optimization Techniques:**
    - Group dates into months/quarters
    - Create category buckets
    - Use derived low-cardinality values

Would you like me to:

1. Show specific examples for your data?
2. Create monitoring queries for your tables?
3. Help optimize your current clustering keys?
4. Demonstrate performance differences with your queries?