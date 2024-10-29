# Create, Delete, Insert vs LEFT ANTI JOIN Vs MErge

LEFT ANTI JOIN  is best because of :
## Performance Benefits:
* Single table scan of each table
* One-time write operation
* No intermediate results to manage
* Combines all logic into one step
* Can leverage clustering immediately


## Data Volume Considerations:
* With large history at 10GB, latest at 160GB, and small searchable_table
* LEFT ANTI JOIN can be optimized by Snowflake's query optimizer better than NOT EXISTS
* INNER JOIN with searchable_table eliminates the need for a separate DELETE


## MERGE would be better if:
* You needed to update existing records
* You were doing incremental loads
* You needed to handle duplicates
