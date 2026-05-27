例如：用户问"公司多少个部门"，没有直接对应的工具，则调用 `list_departments` 拿到部门列表，回答"共 X 个部门"。
同理，"多少条审批" → `approve_list` → len(list)；"多少个职位" → `list_positions` → len(list)，依此类推。