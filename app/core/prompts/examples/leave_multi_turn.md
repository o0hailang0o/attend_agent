## 请假流程示例

### 多轮对话（必须每次都调 register_leave）

第1轮：用户"明天下午请个假"
→ 意图：请假。虽然缺少请假类型、原因、审批人，但必须立即调用 register_leave：
TOOL_CALL: {"tool": "register_leave", "params": {"leave_type": "", "range": "明天下午", "reason": "", "leader": ""}}

（register_leave 返回："还需要提供以下信息：请假类型、请假原因、审批人"——此时不要自己问，等用户回复）

第2轮：用户"年假"
→ 结合上一轮上下文，用户是在回答「请假类型」问题，不是查询余额 → 补齐 leave_type：
TOOL_CALL: {"tool": "register_leave", "params": {"leave_type": "年假", "range": "明天下午", "reason": "", "leader": ""}}

（register_leave 返回："还需要提供以下信息：请假原因、审批人"）

第3轮：用户"家里有事"
→ 补齐 reason：
TOOL_CALL: {"tool": "register_leave", "params": {"leave_type": "年假", "range": "明天下午", "reason": "家里有事", "leader": ""}}

（register_leave 返回："还需要提供以下信息：审批人"）

第4轮：用户"张三"
→ 补齐 leader：
TOOL_CALL: {"tool": "register_leave", "params": {"leave_type": "年假", "range": "明天下午", "reason": "家里有事", "leader": "张三"}}

（register_leave 返回请假单摘要，提示确认）

### 信息一次给全时仍然调用工具
用户："帮我提交明天下午2点到4点的年假，家里有急事，审批人张三"
→ 一次识别全部参数，直接调用：
TOOL_CALL: {"tool": "register_leave", "params": {"leave_type": "年假", "range": "明天下午2点到4点", "reason": "家里有急事", "leader": "张三"}}

（register_leave 返回确认卡片，等用户确认后再次调用并传 confirmed=true）
