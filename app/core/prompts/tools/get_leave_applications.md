### get_leave_applications
- 功能：获取请假申请列表，返回申请记录（开始时间、结束时间、类型、状态、原因等）
- 参数：`employee_identifier`（员工姓名或工号，传空字符串时查当前用户；传具体姓名/工号时查该员工）
- 返回字段：startTime 开始、endTime 结束、type 类型、statusName 状态名称、reason 事由、reject 驳回原因