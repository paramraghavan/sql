import snowflake.connector
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import logging
import uuid


class TempTableParallelUpdater:
    def __init__(self, connection_params: Dict):
        self.connection_params = connection_params
        self.session_id = str(uuid.uuid4())[:8]  # For unique temp table names
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _execute_sql(self, sql: str) -> Dict:
        """Execute a SQL statement and return results"""
        conn = snowflake.connector.connect(**self.connection_params)
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            return {'status': 'success', 'rowcount': cursor.rowcount}
        except Exception as e:
            self.logger.error(f"SQL execution failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
        finally:
            conn.close()

    def _create_temp_tables(self, table_name: str, num_partitions: int) -> bool:
        """Create temporary tables for each partition"""
        try:
            for i in range(num_partitions):
                partition_sql = f"""
                CREATE TEMPORARY TABLE tmp_{self.session_id}_p{i} AS
                SELECT *
                FROM {table_name}
                WHERE MOD(ABS(HASH(CONCAT(search_id, 
                      TO_CHAR(search_dt, 'YYYY-MM-DD HH24:MI:SS')))), 
                      {num_partitions}) = {i}
                """
                result = self._execute_sql(partition_sql)
                if result['status'] == 'error':
                    self._cleanup_temp_tables(num_partitions)
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to create temp tables: {str(e)}")
            self._cleanup_temp_tables(num_partitions)
            return False

    def _update_partition(self, partition_id: int, update_sql: str) -> Dict:
        """Execute update on a single partition's temp table"""
        conn = snowflake.connector.connect(**self.connection_params)
        try:
            cursor = conn.cursor()
            # Modify the update SQL to use temp table
            temp_table = f"tmp_{self.session_id}_p{partition_id}"
            modified_sql = update_sql.replace(
                "your_table", temp_table
            )
            cursor.execute(modified_sql)
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

    def _merge_temp_tables(self, table_name: str, num_partitions: int) -> Dict:
        """Merge all temp tables back into the original table"""
        merge_sql = f"""
        MERGE INTO {table_name} t
        USING (
            {' UNION ALL '.join([
            f"SELECT * FROM tmp_{self.session_id}_p{i}"
            for i in range(num_partitions)
        ])}
        ) s
        ON t.search_id = s.search_id 
        AND t.search_dt = s.search_dt
        WHEN MATCHED THEN UPDATE SET
        """

        # Get column list from the first temp table
        conn = snowflake.connector.connect(**self.connection_params)
        try:
            cursor = conn.cursor()
            cursor.execute(f"DESC TABLE tmp_{self.session_id}_p0")
            columns = [row[0] for row in cursor if row[0].lower() not in ('search_id', 'search_dt')]
            set_clause = ", ".join([f"t.{col} = s.{col}" for col in columns])
            merge_sql += set_clause

            return self._execute_sql(merge_sql)
        finally:
            conn.close()

    def _cleanup_temp_tables(self, num_partitions: int):
        """Clean up all temporary tables"""
        for i in range(num_partitions):
            self._execute_sql(f"DROP TABLE IF EXISTS tmp_{self.session_id}_p{i}")

    def parallel_update(self, table_name: str, update_sql: str, num_partitions: int = 4) -> Dict:
        """
        Execute parallel updates using temporary tables

        Args:
            table_name: Name of the table to update
            update_sql: UPDATE statement to execute
            num_partitions: Number of partitions to create

        Returns:
            Dictionary with update results
        """
        try:
            # Step 1: Create temp tables
            self.logger.info("Creating temporary partition tables...")
            if not self._create_temp_tables(table_name, num_partitions):
                return {'status': 'error', 'message': 'Failed to create temp tables'}

            # Step 2: Execute parallel updates
            self.logger.info("Executing parallel updates...")
            with ThreadPoolExecutor(max_workers=num_partitions) as executor:
                futures = [
                    executor.submit(self._update_partition, i, update_sql)
                    for i in range(num_partitions)
                ]
                update_results = [future.result() for future in as_completed(futures)]

            # Check if all updates succeeded
            if not all(r['status'] == 'success' for r in update_results):
                raise Exception("One or more partition updates failed")

            # Step 3: Merge results back
            self.logger.info("Merging results back to main table...")
            merge_result = self._merge_temp_tables(table_name, num_partitions)

            return {
                'status': 'success',
                'partition_results': update_results,
                'merge_result': merge_result
            }

        except Exception as e:
            self.logger.error(f"Parallel update failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

        finally:
            # Always clean up temp tables
            self._cleanup_temp_tables(num_partitions)


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
    updater = TempTableParallelUpdater(conn_params)

    # Example update
    update_sql = """
    UPDATE your_table 
    SET col1 = 'new_value',
        col2 = col2 * 1.1,
        last_updt = CURRENT_TIMESTAMP()
    WHERE condition = true
    """

    # Execute parallel update
    results = updater.parallel_update(
        table_name='your_table',
        update_sql=update_sql,
        num_partitions=4
    )

    # Print results
    print("\nUpdate Results:")
    print(f"Overall Status: {results['status']}")

    if results['status'] == 'success':
        print("\nPartition Results:")
        for result in results['partition_results']:
            print(f"Partition {result['partition_id']}: {result['rows_updated']} rows updated")

        print(f"\nMerge Result: {results['merge_result']['status']}")
        if results['merge_result']['status'] == 'success':
            print(f"Total Rows Merged: {results['merge_result']['rowcount']}")
    else:
        print(f"Error: {results.get('error', 'Unknown error')}")

# Example of multiple updates:
"""
# List of updates to perform
updates = [
    {
        'sql': "UPDATE your_table SET status = 'PROCESSED' WHERE status = 'PENDING'",
        'partitions': 4
    },
    {
        'sql': "UPDATE your_table SET amount = amount * 1.1 WHERE category = 'STANDARD'",
        'partitions': 6
    }
]

# Execute all updates
for update in updates:
    print(f"\nExecuting update: {update['sql'][:50]}...")
    results = updater.parallel_update(
        table_name='your_table',
        update_sql=update['sql'],
        num_partitions=update['partitions']
    )
"""
