Creating a Python script using boto3 to query AWS Athena for S3 access logs.

```python
import boto3
import time
import json
from datetime import datetime


def query_s3_logs(database, table, request_param_value):
    """
    Query S3 logs using Athena filtering by GetObject and PutObject events
    and specific request parameter value
    
    Args:
        database (str): Athena database name
        table (str): Table name containing S3 logs
        request_param_value (str): Value to filter in requestParameters
    
    Returns:
        str: Query results in JSON format
    """
    athena_client = boto3.client('athena')

    # Query to filter S3 logs
    query = f"""
    SELECT 
        eventtime,
        eventname,
        awsregion,
        sourceipaddress,
        useragent,
        requestparameters,
        responseelements
    FROM {database}.{table}
    WHERE eventname IN ('GetObject', 'PutObject')
    AND requestparameters LIKE '%{request_param_value}%'
    LIMIT 100
    """

    # Start query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': database
        },
        ResultConfiguration={
            'OutputLocation': 's3://your-query-results-bucket/folder/'  # Replace with your bucket
        }
    )

    query_execution_id = response['QueryExecutionId']

    # Wait for query to complete
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        state = response['QueryExecution']['Status']['State']

        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break

        time.sleep(1)

    if state != 'SUCCEEDED':
        raise Exception(f"Query failed with state: {state}")

    # Get query results
    results = athena_client.get_query_results(QueryExecutionId=query_execution_id)

    # Process results
    processed_results = []
    headers = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]

    for row in results['ResultSet']['Rows'][1:]:  # Skip header row
        values = [field.get('VarCharValue', '') for field in row['Data']]
        processed_results.append(dict(zip(headers, values)))

    # Function to convert results to different formats
    def format_results(format_type='json'):
        if format_type == 'json':
            return json.dumps(processed_results, indent=2)
        elif format_type == 'csv':
            csv_data = ','.join(headers) + '\n'
            for result in processed_results:
                csv_data += ','.join(str(result[header]) for header in headers) + '\n'
            return csv_data
        else:
            return str(processed_results)

    return format_results('json')  # Change format type here if needed


# Example usage
if __name__ == "__main__":
    try:
        results = query_s3_logs(
            database='your_database_name',
            table='your_table_name',
            request_param_value='your_search_value'
        )
        print(results)
    except Exception as e:
        print(f"Error: {str(e)}")

```

To use this script, you'll need to:

1. Replace the placeholder values:
    - `your-query-results-bucket/folder/` with your S3 bucket path for Athena results
    - `your_database_name` with your Athena database name
    - `your_table_name` with your table name
    - `your_search_value` with the value you want to search in requestParameters

2. Ensure you have proper AWS credentials configured (either through AWS CLI or environment variables)

3. Install required package:

```bash
pip install boto3
```

The script:

- Queries Athena for S3 logs filtering by GetObject and PutObject events
- Filters results by your specified requestParameters value
- Limits results to 100 matches
- Returns results in JSON format (can be modified to CSV or string)
- Includes error handling and query status checking
- Returns relevant fields like eventtime, eventname, region, source IP, etc.

You can modify the format of the results by changing the format type in the `format_results()` call at the end of the
function (options: 'json', 'csv', or 'string').


```
import boto3

athena_client = boto3.client('athena')

def list_all_tables(database_name):
    tables = []
    paginator = athena_client.get_paginator('list_table_metadata')
    
    try:
        for page in paginator.paginate(
            CatalogName='AwsDataCatalog',
            DatabaseName=database_name
        ):
            for table in page['TableMetadataList']:
                tables.append(table['Name'])
                
        return tables
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Use the function
tables = list_all_tables('cloudtrail_analysis')
if tables:
    print("Tables found:")
    for table in tables:
        print(f"- {table}")
```

