SELECT count(*) ,year(date),month(date)from messagelog_message
group by year(date),month(date)
order by year(date),month(date);

SELECT * from messagelog_message