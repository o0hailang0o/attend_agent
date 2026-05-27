# AGENTS.md — attend_agent

企业考勤智能助手 — attendance AI agent with natural language chat.

## Stack

- **Framework**: FastAPI (async), Python 3.11, Poetry
- **LLM**: LlamaIndex 0.12 + OpenAI (GPT-4o-mini), function calling
- **Database**: MySQL via async SQLAlchemy + aiomysql (`attend_agent` database)
- **Cache**: async Redis (aioredis)
- **No tests, no linter, no type checker** configured

## Run

```bash
poetry run python -m app.main
# or: uvicorn app.main:app --reload
```

Server on `http://localhost:8000`, debug mode (hot reload + SQL echo).

## User lookup

`app/utils/user_lookup.py` → `resolve_user(identifier)` 自动判断姓名/工号并查询 `sys_user` 表返回 `(uuid, name)`。在 function_calling 各工具中自动调用，支持：
- 纯数字 → 匹配 `account` 或 `work_num`
- 中文名 → 精确匹配 `name`，未匹配时 LIKE 模糊查询

## Setup

1. `poetry install`
2. Copy or edit `settings.yml` — **must set `llm.api_key`** (it is empty by default).

## Architecture

```
app/main.py  →  FastAPI app, lifespan (init/close Redis)
                routes: /api/v1/chat, /api/v1/attendance/*, /health

app/core/
├── config.py       # Loads settings.yml via pydantic-settings
├── database.py     # AsyncSession via async_sessionmaker, get_db() dependency
├── redis.py        # Global aioredis singleton, init/close in lifespan
└── llama_index.py  # Global OpenAI LLM singleton, sets LlamaSettings.llm

app/models/         # SQLAlchemy ORM: Employee, AttendanceRecord, Leave, OvertimeRecord
app/schemas/        # Pydantic request/response models (from_attributes=True)
app/services/
├── attendance.py       # 本地 DB 查询（FastAPI route 使用）
├── function_calling/   # LlamaIndex function tools（LLM 调用，按 controller 分包）
│   ├── __init__.py         # get_available_tools() 聚合所有工具
│   ├── daily_attendance.py # 考勤查询/汇总/加班
│   ├── leave.py            # 请假登记/假期余额
│   ├── sys_user.py         # 员工查询
│   ├── door_access.py      # 门禁记录
│   ├── approve.py          # 审批通过/驳回
│   ├── leader.py           # 领导列表
│   ├── dept.py             # 部门列表
│   ├── position.py         # 职位列表
│   └── rule.py             # 考勤规则
└── attend_api/         # httpx 调用 attend 工程的 Spring Boot controller 接口
    ├── base.py              # 共享 httpx 客户端（GET/POST/PUT/DELETE），封装 Result 解析
    ├── daily_attendance.py  # DailyAttendanceController → /dailyAttendance
    ├── leave_balance.py     # LeaveBalanceController → /leaveBalance
    ├── apply.py             # ApplyController → /apply
    ├── sys_user.py          # SysUserController → /sysuser
    ├── door_access.py       # DoorAccessController → /doorAccess
    ├── approve.py           # ApproveController → /approve
    ├── leader.py            # LeaderController → /leader
    ├── position.py          # PositionController → /position
    ├── dept.py              # DeptController → /dept
    └── rule.py              # RuleController → /rule
app/api/routes/     # FastAPI route handlers
```

## Key detail: httpx calls the attend backend

The LLM function-calling tools (`app/services/function_calling.py`) call **attend 工程的 Spring Boot controller 接口** (port 8080) via synchronous `httpx`:

```python
ATTEND_BASE_URL = "http://localhost:8080"
```

响应格式为 `{"code": 200, "data": ..., "msg": "..."}`。

| 函数 | 调用的 attend 接口 |
|---|---|
| `get_employee_attendance` | `GET /dailyAttendance?employeeUuid={id}&date={date}` |
| `get_attendance_summary` | `GET /dailyAttendance?date={date}` + 本地按状态聚合 |
| `get_overtime_records` | `GET /dailyAttendance?employeeUuid={id}&startDate=...&endDate=...` (过滤 `actualWorkHours > 8`) |
| `register_leave` | `POST /apply` (映射 `leave_type` → 整数 type) |
| `get_leave_balance` | `GET /leaveBalance/byAccount?account={id}` |

## Chat flow

1. `POST /api/v1/chat` with `{"message": "..."}`
2. LlamaIndex LLM (OpenAI) receives the message + tool definitions
3. If LLM decides to call a tool, the handler executes the tool function via sync httpx to the attend 工程的 Spring Boot controller 接口
4. Tools return plain-text strings, which become part of the LLM's reply

## Conventions

- All UI-facing text is **Chinese (zh-CN)**.
- Settings loaded from `settings.yml` (same directory as `pyproject.toml`), **not** from env vars.
- Database tables: `employees`, `attendance_records`, `leaves`, `overtime_records` — separate from the `attend` backend's DB.
- Model IDs are auto-increment integers (not UUIDs like the `attend` backend).
- No Alembic / migrations — schema is defined purely in SQLAlchemy models.
