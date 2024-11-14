Setup access to Snowflake logging via Athena, we need to set up a pipeline where Snowflake logs are exported to S3 and then
create an Athena table to query them. Here's how to set this up:

```sql
-- Step 1: In Snowflake, create storage integration for S3
CREATE OR REPLACE STORAGE INTEGRATION s3_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::your-account-id:role/snowflake-access-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-bucket/snowflake-logs/');

-- Step 2: Create Snowflake stage
CREATE OR REPLACE STAGE snowflake_logs_stage
  STORAGE_INTEGRATION = s3_int
  URL = 's3://your-bucket/snowflake-logs/'
  FILE_FORMAT = (TYPE = JSON);

-- Step 3: Create Snowflake task to export logs
CREATE OR REPLACE TASK export_logs_task
  WAREHOUSE = your_warehouse
  SCHEDULE = 'USING CRON 0 */1 * * * America/New_York'
AS
COPY INTO @snowflake_logs_stage/
FROM (
    SELECT *
    FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
    WHERE START_TIME >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
)
FILE_FORMAT = (TYPE = JSON)
OVERWRITE = FALSE;

-- Step 4: Create Athena table to read Snowflake logs
CREATE EXTERNAL TABLE snowflake_logs (
    query_id STRING,
    query_text STRING,
    database_name STRING,
    schema_name STRING,
    query_type STRING,
    session_id STRING,
    user_name STRING,
    role_name STRING,
    warehouse_name STRING,
    warehouse_size STRING,
    warehouse_type STRING,
    cluster_number STRING,
    query_tag STRING,
    execution_status STRING,
    error_code STRING,
    error_message STRING,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_elapsed_time BIGINT,
    bytes_scanned BIGINT,
    rows_produced BIGINT,
    compilation_time BIGINT,
    execution_time BIGINT,
    queued_provisioning_time BIGINT,
    queued_repair_time BIGINT,
    queued_overload_time BIGINT,
    transaction_blocked_time BIGINT,
    outbound_data_transfer_cloud STRING,
    outbound_data_transfer_region STRING,
    outbound_data_transfer_bytes BIGINT,
    inbound_data_transfer_cloud STRING,
    inbound_data_transfer_region STRING,
    inbound_data_transfer_bytes BIGINT,
    credits_used_cloud_services DECIMAL(38,9)
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://your-bucket/snowflake-logs/';

```

Here's the step-by-step implementation process:

1. **AWS IAM Setup**:

```python
import boto3
import json


def create_snowflake_iam_role():
    iam = boto3.client('iam')

    # Create IAM role
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::your-snowflake-account:user/snowflake"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    # Create role
    response = iam.create_role(
        RoleName='snowflake-access-role',
        AssumeRolePolicyDocument=json.dumps(role_policy)
    )

    # Attach S3 policy
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:DeleteObject",
                    "s3:DeleteObjectVersion"
                ],
                "Resource": "arn:aws:s3:::your-bucket/snowflake-logs/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": "arn:aws:s3:::your-bucket"
            }
        ]
    }

    iam.put_role_policy(
        RoleName='snowflake-access-role',
        PolicyName='snowflake-s3-access',
        PolicyDocument=json.dumps(s3_policy)
    )
```

2. **Implementation Steps**:

   a. **Create S3 Bucket** (if not exists):
   ```python
   def create_s3_bucket():
       s3 = boto3.client('s3')
       bucket_name = 'your-bucket'
       
       s3.create_bucket(
           Bucket=bucket_name,
           CreateBucketConfiguration={
               'LocationConstraint': 'your-region'
           }
       )
   ```

   b. **Execute Snowflake Setup**:
    - Run the storage integration creation SQL
    - Get the AWS IAM user from Snowflake:
   ```sql
   DESC STORAGE INTEGRATION s3_int;
   ```
    - Create the stage and task
    - Start the task:
   ```sql
   ALTER TASK export_logs_task RESUME;
   ```

   c. **Create Athena Database** (if needed):
   ```sql
   CREATE DATABASE IF NOT EXISTS snowflake_logs_db;
   ```

3. **Verification Queries**:

```sql
-- Test query in Athena
SELECT 
    query_id,
    user_name,
    warehouse_name,
    query_type,
    start_time,
    total_elapsed_time,
    credits_used_cloud_services
FROM snowflake_logs
WHERE start_time >= CURRENT_DATE - INTERVAL '1' DAY
ORDER BY start_time DESC
LIMIT 10;
```

4. **Important Considerations**:

- Ensure your Snowflake role has ACCOUNTADMIN or appropriate privileges
- The AWS IAM role needs proper permissions for S3
- Configure appropriate partitioning if dealing with large volumes of logs
- Consider data retention policies
- Monitor storage costs
- Set up appropriate table partitioning if needed

5. **Optional: Add Partitioning**:

```sql
-- Create partitioned table in Athena
CREATE EXTERNAL TABLE snowflake_logs_partitioned (
    -- same columns as above
)
PARTITIONED BY (
    date_partition STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://your-bucket/snowflake-logs/';

-- Add partition
ALTER TABLE snowflake_logs_partitioned ADD
PARTITION (date_partition='2024-11-13')
LOCATION 's3://your-bucket/snowflake-logs/2024/11/13/';
```
