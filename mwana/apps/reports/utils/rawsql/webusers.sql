--SELECT * from webreports_groupfacilitymapping
--SELECT * FROM webreports_groupusermapping
SELECT name as "Group Name",count(user_id) as "Users Accounts" FROM webreports_reportinggroup
join webreports_groupusermapping on webreports_reportinggroup.id=webreports_groupusermapping.group_id
group by name
order by 2