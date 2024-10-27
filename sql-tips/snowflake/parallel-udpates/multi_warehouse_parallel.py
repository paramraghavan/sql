import snowflake.connector
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Union
import logging


class MultiWarehouseUpdater:
    def __init__(self, base_connection_params: Dict):
        """
        Initialize with base Snowflake connection parameters
        The warehouse parameter will be overridden per partition if specified
        """
        self.base_connection_params = base_connection_params
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _execute_update(self,
                        partition_id: int,
                        update_sql: str,
                        num_partitions: int,
                        warehouse: str = None) -> Dict:
        """Execute update for a single partition using specified warehouse"""
        # Create connection params with specific warehouse if provided
        conn_params = self.base_connection_params.copy()
        if warehouse:
            conn_params['warehouse'] = warehouse

        conn = snowflake.connector.connect(**conn_params)
        try:
            cursor = conn.cursor()

            # Use specified warehouse
            if warehouse:
                cursor.execute(f"USE WAREHOUSE {warehouse}")

            partitioned_sql = f"""
                {update_sql}
                AND MOD(ABS(HASH(CONCAT(search_id, 
                    TO_CHAR(search_dt, 'YYYY-MM-DD HH24:MI:SS')))), 
                    {num_partitions}) = {partition_id}
            """
            cursor.execute(partitioned_sql)
            return {
                'partition_id': partition_id,
                'warehouse': warehouse or conn_params.get('warehouse', 'default'),
                'rows_updated': cursor.rowcount,
                'status': 'success'
            }
        except Exception as e:
            self.logger.error(f"Partition {partition_id} failed on warehouse {warehouse}: {str(e)}")
            return {
                'partition_id': partition_id,
                'warehouse': warehouse,
                'status': 'error',
                'error': str(e)
            }
        finally:
            conn.close()

    def parallel_update(self,
                        update_sql: str,
                        num_partitions: int = 4,
                        warehouses: Union[List[str], str] = None) -> List[Dict]:
        """
        Execute update in parallel across partitions using specified warehouses

        Args:
            update_sql: SQL UPDATE statement (without WHERE clause)
            num_partitions: Number of parallel updates to perform
            warehouses: Either a list of warehouse names (one per partition)
                       or a single warehouse name to use for all partitions
                       If None, uses the warehouse from connection params
        """
        # Handle warehouse specification
        if isinstance(warehouses, str):
            warehouse_list = [warehouses] * num_partitions
        elif isinstance(warehouses, list):
            if len(warehouses) != num_partitions:
                raise ValueError(
                    f"Number of warehouses ({len(warehouses)}) must match number of partitions ({num_partitions})")
            warehouse_list = warehouses
        else:
            warehouse_list = [None] * num_partitions

        with ThreadPoolExecutor(max_workers=num_partitions) as executor:
            futures = [
                executor.submit(
                    self._execute_update,
                    i,
                    update_sql,
                    num_partitions,
                    warehouse_list[i]
                )
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
        'database': 'your_database',
        'schema': 'your_schema'
        # Default warehouse not specified here as we'll use specific ones
    }

    # Create updater instance
    updater = MultiWarehouseUpdater(conn_params)

    # Example 1: Using different warehouses for each partition
    warehouses = [
        'WAREHOUSE_PARTITION_1',
        'WAREHOUSE_PARTITION_2',
        'WAREHOUSE_PARTITION_3',
        'WAREHOUSE_PARTITION_4'
    ]

    update_sql = """
    UPDATE your_table 
    SET col1 = 'new_value'
    WHERE condition = true
    """

    # Execute update using different warehouses
    results = updater.parallel_update(
        update_sql=update_sql,
        num_partitions=4,
        warehouses=warehouses
    )

    # Print results
    print("\nUpdate Results:")
    total_rows = 0
    for r in results:
        if r['status'] == 'success':
            print(f"Partition {r['partition_id']} on warehouse {r['warehouse']}: {r['rows_updated']} rows updated")
            total_rows += r['rows_updated']
        else:
            print(f"Partition {r['partition_id']} on warehouse {r['warehouse']} failed: {r['error']}")

    print(f"\nTotal rows updated: {total_rows}")

    # Example 2: Using single warehouse for all partitions
    results = updater.parallel_update(
        update_sql=update_sql,
        num_partitions=4,
        warehouses='SINGLE_LARGE_WAREHOUSE'
    )

    # Example 3: Different updates with different warehouse configurations
    updates = [
        {
            'sql': "UPDATE your_table SET status = 'PROCESSED' WHERE status = 'PENDING'",
            'warehouses': ['WH1', 'WH2', 'WH3', 'WH4']
        },
        {
            'sql': "UPDATE your_table SET amount = amount * 1.1 WHERE category = 'STANDARD'",
            'warehouses': 'LARGE_WAREHOUSE'  # Single warehouse for all partitions
        },
        {
            'sql': "UPDATE your_table SET last_updated = CURRENT_TIMESTAMP() WHERE date_column < '2024-01-01'",
            'warehouses': ['WH_A', 'WH_B']  # Using 2 partitions only
        }
    ]

    for update in updates:
        num_partitions = len(update['warehouses']) if isinstance(update['warehouses'], list) else 4
        results = updater.parallel_update(
            update_sql=update['sql'],
            num_partitions=num_partitions,
            warehouses=update['warehouses']
        )

        # Process results...
