### get_employee_attendance
- 功能：查询单个员工某天的考勤记录，返回上班时间、下班时间、实际工时、考勤状态、日类型
- 参数：`employee_identifier`（员工姓名或工号，为空查当前用户），`date`（日期，支持今天/昨天/周一等自然语言）
- 返回字段：employeeName 姓名、date 日期、clockIn 上班、clockOut 下班、actualWorkHours 实际工时、statusName 考勤状态（正常/迟到/早退/缺勤/补正）、dayTypeName 日类型