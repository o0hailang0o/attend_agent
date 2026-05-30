## 多工具组合示例

### 同时查询多项数据
用户："张三昨天的打卡记录和门禁记录"
→ 需要两个工具，同时调用：
TOOL_CALL: {"tool": "get_employee_attendance", "params": {"employee_identifier": "张三", "date": "昨天"}}
TOOL_CALL: {"tool": "get_door_access", "params": {"employee_identifier": "张三", "date": "昨天"}}

### 对比查询
用户："我和张三谁的年假多"
→ 同时查两个人的余额：
TOOL_CALL: {"tool": "get_leave_balance", "params": {"employee_identifier": ""}}
TOOL_CALL: {"tool": "get_leave_balance", "params": {"employee_identifier": "张三"}}

### 先查信息再组合
用户："我的部门的考勤规则是什么"
→ 需要组合：search_user 找到自己的部门 → list_rules 查规则
TOOL_CALL: {"tool": "search_user", "params": {"name": ""}}
TOOL_CALL: {"tool": "list_rules", "params": {}}

### 统计类查询（列表转计数）
用户："公司一共有多少个部门"
→ TOOL_CALL: {"tool": "list_departments", "params": {}}
（拿到列表后统计数组长度即为部门数量）

### 条件筛选
用户："产品部有哪些人"
→ TOOL_CALL: {"tool": "search_user", "params": {"name": "产品"}}
（search_user 支持按部门名或姓名模糊搜索）
