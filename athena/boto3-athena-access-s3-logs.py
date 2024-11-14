import boto3
import time
from datetime import datetime, timedelta


def query_s3_logs(database_name, table_name, s3_output_location, request_param_value):
    """
    Query S3 access logs using Athena for GET and PUT operations
    with specific requestParameters value
    """
    athena_client = boto3.client('athena')

    # Query to filter S3 logs
    query = f"""
    SELECT eventtime,
           eventname,
           awsregion,
           sourceipaddress,
           useragent,
           requestparameters,
           errorcode,
           errormessage
    FROM {database_name}.{table_name}
    WHERE eventname IN ('GetObject', 'PutObject')
    AND requestparameters LIKE '%{request_param_value}%'
    LIMIT 100
    """

    # Start query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': database_name
        },
        ResultConfiguration={
            'OutputLocation': s3_output_location
        }
    )

    query_execution_id = response['QueryExecutionId']

    # Wait for query to complete
    while True:
        query_status = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )['QueryExecution']['Status']['State']

        if query_status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break

        time.sleep(1)

    # Check if query failed
    if query_status != 'SUCCEEDED':
        raise Exception(f"Query failed with status: {query_status}")

    # Get query results
    results = athena_client.get_query_results(
        QueryExecutionId=query_execution_id
    )

    return results


def process_results(results):
    """Process and format the query results"""
    processed_results = []

    # Skip the first row as it contains column headers
    for row in results['ResultSet']['Rows'][1:]:
        processed_row = {
            'EventTime': row['Data'][0]['VarCharValue'],
            'EventName': row['Data'][1]['VarCharValue'],
            'AWSRegion': row
