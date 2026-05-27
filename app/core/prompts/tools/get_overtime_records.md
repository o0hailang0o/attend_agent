### get_overtime_records
- 功能：查询员工在日期范围内的加班记录（实际工时 > 8 小时），返回日期、上下班时间、实际工时
- 参数：`employee_identifier`（员工姓名或工号），`start_date`（开始日期），`end_date`（结束日期）
- 返回字段：date 日期、clockIn 上班、clockOut 下班、actualWorkHours 实际工时