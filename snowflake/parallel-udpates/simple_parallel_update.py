import snowflake.connector
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import logging


class SimpleParallelUpdater:
    def __init__(self, connection_params: Dict):
        """Initialize with Snowflake connection parameters"""
        self.connection_params = connection_params
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _execute_update(self, partition_id: int, update_sql: str, num_partitions: int) -> Dict:
        """Execute update for a single partition"""
        conn = snowflake.connector.connect(**self.connection_params)
        try:
            cursor = conn.cursor()
            partitioned_sql = f"""
                {update_sql}
                AND MOD(ABS(HASH(CONCAT(search_id, 
                    TO_CHAR(search_dt, 'YYYY-MM-DD HH24:MI:SS')))), 
                    {num_partitions}) = {partition_id}
            """
            cursor.execute(partitioned_sql)
            return {
                'partition_id': partition_id,
                'rows_updated': cursor.rowcount,
                'status': 'success'
            }
        except Exception as e:
            self.logger.error(f"Partition {partition_id} failed: {str(e)}")
            return {
                'partition_id': partition_id,
                'status': 'error',
                'error': str(e)
            }
        finally:
            conn.close()

    def parallel_update(self, update_sql: str, num_partitions: int = 4) -> List[Dict]:
        """
        Execute update in parallel across partitions

        Args:
            update_sql: SQL UPDATE statement (without WHERE clause)
            num_partitions: Number of parallel updates to perform

        Returns:
            List of results for each partition
        """
        with ThreadPoolExecutor(max_workers=num_partitions) as executor:
            futures = [
                executor.submit(self._execute_update, i, update_sql, num_partitions)
                for i in range(num_partitions)
            ]
            return [future.result() for future in as_completed(futures)]


# Example usage
if __name__ == "__main__":
    # Connection parameters
    conn_params = {
        'user': 'your_username',
        'password': 'your_password',
        'account': 'your_account',
        'warehouse': 'your_warehouse',
        'database': 'your_database',
        'schema': 'your_schema'
    }

    # Create updater instance
    updater = SimpleParallelUpdater(conn_params)

    # Example updates you might want to perform
    updates = [
        """
        UPDATE your_table 
        SET col1 = 'new_value1'
        WHERE col2 = 'condition1'
        """,

        """
        UPDATE your_table 
        SET col3 = col3 * 1.1
        WHERE col4 > 100
        """,

        """
        UPDATE your_table 
        SET col5 = CURRENT_TIMESTAMP()
        WHERE col6 IS NULL
        """
    ]

    # Execute each update in parallel
    for update_sql in updates:
        print(f"\nExecuting update: {update_sql[:50]}...")
        results = updater.parallel_update(update_sql, num_partitions=4)

        # Print results
        total_rows = sum(r['rows_updated'] for r in results if r['status'] == 'success')
        print(f"Total rows updated: {total_rows}")

        # Check for any errors
        errors = [r for r in results if r['status'] == 'error']
        if errors:
            print("Errors encountered:")
            for error in errors:
                print(f"Partition {error['partition_id']}: {error['error']}")

# Examples of different types of updates:
"""
# Example 1: Simple value update
results = updater.parallel_update(
    "UPDATE your_table SET status = 'PROCESSED' WHERE status = 'PENDING'"
)

# Example 2: Calculated update
results = updater.parallel_update(
    "UPDATE your_table SET amount = amount * 1.1 WHERE category = 'STANDARD'"
)

# Example 3: Date-based update
results = updater.parallel_update(
    "UPDATE your_table SET last_updated = CURRENT_TIMESTAMP() WHERE date_column < '2024-01-01'"
)

# Example 4: Complex condition update
results = updater.parallel_update('''
    UPDATE your_table 
    SET status = 'EXPIRED',
        updated_by = 'SYSTEM'
    WHERE amount < 1000 
    AND date_column < DATEADD(day, -30, CURRENT_DATE())
''')
"""
