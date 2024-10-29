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



```sql
-- history and latest are very large tables and searchable_table is a small table
-- You can check clustering depth with
SELECT SYSTEM$CLUSTERING_DEPTH('history');

-- Monitor clustering information
SELECT SYSTEM$CLUSTERING_INFORMATION('history');

-- If needed, you can manually reclustering
ALTER TABLE history RECLUSTER;

ALTER TABLE history CLUSTER BY (search_id, search_dt);
ALTER TABLE latest CLUSTER BY (search_id, search_dt);

CREATE TABLE temp_table 
-- if these cols are used for updates
CLUSTER BY(search_id, search_dt) 
AS
SELECT a.search_id, a.search_dt, a.last_updt
FROM history a
LEFT ANTI JOIN latest b
    ON a.search_id = b.search_id 
    AND a.search_dt = b.search_dt
INNER JOIN searchable_table s 
    ON a.search_id = s.search_id;
    


CREATE TABLE temp_table AS
SELECT a.search_id, a.search_dt, a.last_updt,  -999 as col1, -999 as col2 
FROM history a
LEFT ANTI JOIN latest b
    ON a.search_id = b.search_id 
    AND a.search_dt = b.search_dt
INNER JOIN searchable_table s 
    ON a.search_id = s.search_id;
    
    
create table temp_table as 
select  
search_id, 
search_dt,
 -999 as col1,
 -999 as col2 
 from history;    
 
 
 -- split the temp_table into multiple temp table
 -- run udpates in separate thread and warehouse per temp_table
 -- join these table back into original table.
 
 
```
