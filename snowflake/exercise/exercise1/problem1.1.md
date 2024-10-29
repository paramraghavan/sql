I have a large table in snowfalke with 160gb data called history which will be updated (where effective date is >
2022-10-01 ) in many steps -4 to 7 steps.
Want to subset data into a temp table where effective date is > 2023-10-01 and create it into 4 separate partitions on
temp_table1 thru temp_table4 for parallel udpates
Apply udpates to temp_table1 thru temp_table4 , once updates are applied and merge these 4 temp tables back to the
hsitory table

do i need to partition the table at all with pyspark ?