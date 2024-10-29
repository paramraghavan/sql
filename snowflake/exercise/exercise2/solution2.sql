
-- history and mortgage are very large tables and security is a small table
-- You can check clustering depth with
SELECT SYSTEM$CLUSTERING_DEPTH('mortgage');

-- Monitor clustering information
SELECT SYSTEM$CLUSTERING_INFORMATION('history');

-- If needed, you can manually reclustering
ALTER TABLE history RECLUSTER;

-- Clustering will not help if the cardinality os less than 20%
-- see
ALTER TABLE history CLUSTER BY (col1, col2);
ALTER TABLE mortgage CLUSTER BY (col1, col2);

CREATE TABLE temp_table
-- if these cols are used for updates
CLUSTER BY(col1, col2)
AS
SELECT a.col1, a.col2, a.col3
 -999 as col4,
 -999 as col5
FROM history a
LEFT ANTI JOIN latest b
    ON a.col1 = b.col1
    AND a.col2 = b.col2
INNER JOIN searchable_table s
    ON a.col1 = s.col1;
