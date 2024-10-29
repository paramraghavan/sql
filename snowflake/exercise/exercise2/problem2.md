I have tables mortgage_pool, history  and security table
- mortgage_pool very large table about 150 to 200 gb
- history table 10 - 20 gb
- security  table small 100mb

Join columns sec_id and effective_date

insert into tmp_table(col1, col2, col3)
select col1, col2, col3 from history  a where not exists
(select col1, col2, col3 from mortgage_pool b
 where a.col1=b.col2 and a.col2=b.col2)

delete from tmp_table where col1 not in( select col1 from security) 

update tmp_table
set
col1=-999,
col2=-999
coln=-999;

Rewrite the above