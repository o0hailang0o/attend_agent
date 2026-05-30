## 上下文衔接示例

### 省略主语
- 第1轮：用户"张三今天考勤怎么样" → TOOL_CALL: {"tool": "get_employee_attendance", "params": {"employee_identifier": "张三", "date": "今天"}}
- 第2轮：用户"昨天呢" → 推理：省略了主语"张三"，补全 → TOOL_CALL: {"tool": "get_employee_attendance", "params": {"employee_identifier": "张三", "date": "昨天"}}

### 省略时间
- 第1轮：用户"这周一全员出勤情况" → TOOL_CALL: {"tool": "get_attendance_summary", "params": {"date": "本周一"}}
- 第2轮：用户"周二呢" → 推理：省略了动作"出勤汇总"，补全 → TOOL_CALL: {"tool": "get_attendance_summary", "params": {"date": "本周二"}}

### 省略动作
- 第1轮：用户"帮我查下张三的请假记录" → TOOL_CALL: {"tool": "get_leave_applications", "params": {"employee_identifier": "张三"}}
- 第2轮：用户"那李四呢" → 推理："那...呢"指代同样的动作"查请假记录" → TOOL_CALL: {"tool": "get_leave_applications", "params": {"employee_identifier": "李四"}}

### 指代消解
- 用户"我今天打卡了吗" → employee_identifier=""（空=当前用户），date="今天"
- 用户"我的年假还剩多少" → employee_identifier=""，调 get_leave_balance
