from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, current_timestamp
import snowflake.connector


def update_history_table():
    # Initialize Spark Session with optimized configs for large data (160GB)
    spark = SparkSession.builder\
    .appName("History Table Updates") \
    .config("spark.sql.shuffle.partitions", "200")\ # Adjust based on data size
    .config("spark.memory.fraction", "0.8")\
    .config("spark.executor.memory", "16g")\
    .config("spark.jars", "snowflake-jdbc-3.13.22.jar,spark-snowflake_2.12-2.11.0-spark_3.3.jar")\
    .getOrCreate()

# Snowflake connection parameters
snowflake_options = {
    "sfURL": "your_account.snowflakecomputing.com",
    "sfUser": "username",
    "sfPassword": "password",
    "sfDatabase": "your_database",
    "sfSchema": "your_schema",
    "sfWarehouse": "your_warehouse"
}

# Step 1: Read only the relevant subset of history table
history_df = spark.read\
.format("net.snowflake.spark.snowflake")\
.options(**snowflake_options)\
.option("query", """
            SELECT * 
            FROM history 
            WHERE effective_date > '2022-10-01'
        """)\
.load()

# Cache the DataFrame since we'll be performing multiple operations
history_df.cache()

# Define your update operations
update_operations = [
    {
        "source_table": "update_table_1",
        "join_condition": "history.id = update_table_1.id",
        "update_columns": {"col1": "update_table_1.new_value1"}
    },
    # Add more update operations as needed
]

# Apply all updates in sequence, but each operation processes in parallel
updated_df = history_df
for operation in update_operations:
    # Read source table for updates
    source_options = snowflake_options.copy()
    source_options["dbtable"] = operation["source_table"]
    source_df = spark.read\
    .format("net.snowflake.spark.snowflake")\
    .options(**source_options)\
    .load()

# Join and update - PySpark handles the parallelization
updated_df = updated_df.join(\
    source_df,\
    spark.sql(operation["join_condition"]),\
    "left"
)

# Apply updates for this operation
for target_col, source_col in operation["update_columns"].items():
    updated_df = updated_df.withColumn(
        target_col,
        when(col(source_col).isNotNull(), col(source_col))
        .otherwise(col(target_col))
    )

# Add last_updated timestamp
updated_df = updated_df.withColumn("last_updated", current_timestamp())

# Write back to Snowflake using merge capability
updated_df.write\
.format("net.snowflake.spark.snowflake")\
.options(**snowflake_options)\
.option("dbtable", "history")\
.option("sfSchema", snowflake_options["sfSchema"])\
.option("sf_merge_keys", "id") \  # Specify your merge key
.mode("merge")\
.save()

# Clear cache
history_df.unpersist()

if __name__ == "__main__":
    update_history_table()
