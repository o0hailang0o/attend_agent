# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Enterprise attendance intelligent assistant (考勤智能助手). A FastAPI service that uses LLM function calling + text-to-SQL to answer natural-language attendance queries, submit leave requests, and manage approvals — backed by a remote attend management system.

## Commands

```bash
# Install dependencies
poetry install

# Run dev server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run a single script for ad-hoc testing
poetry run python -c "from app.utils.date_converter import DateConverter; print(DateConverter.parse_date('今天'))"
```

No test suite or lint configuration exists in this repo.

## Architecture

### Request flow

```
Request → auth middleware (Redis token → ContextVar)
         → chat endpoint: loads history, then runs two paths in parallel:
           1. function_calling: LLM decides tools → TOOL_CALL: JSON lines → _execute_tool → attend API or DB
           2. text_to_sql: LLM generates SQL → raw MySQL execution
         → merge results → master LLM synthesizes final reply
```

### Two-path strategy

The chat endpoint (`app/api/routes/chat.py`) fires **both** function_calling and text_to_sql in parallel using `asyncio.to_thread`. The function_calling path gets 60s timeout; text_to_sql gets an additional 10s after function_calling completes. This means structured tool results always arrive first, and SQL query results are appended as bonus context if they finish in time.

### Function calling

- `app/services/function_calling/__init__.py` registers all available tools as LlamaIndex `FunctionTool` instances.
- Each tool in `app/services/function_calling/` is a Python function with a detailed docstring (used as the tool description for the LLM). It calls a corresponding controller in `app/services/attend_api/` which wraps the remote attend backend HTTP API.
- The LLM responds with `TOOL_CALL: {"tool": "...", "params": {...}}` lines parsed by `_parse_tool_calls`.
- Leave application (`register_leave`) supports multi-turn: if parameters are missing, it returns guidance and sets `pending_tool_call` ContextVar so the next chat turn can continue collecting parameters.

### Text-to-SQL

- `app/services/text_to_sql/__init__.py` contains a hardcoded schema description and prompt template.
- A **separate LLM instance** (`get_text_to_sql_llm()`) is used to generate SQL, configurable with a different model via `text-to-sql-llm` in settings.yml.
- Generated SQL is executed directly against the MySQL `attend` database (read-only queries).
- The user's UUID is injected into the prompt so queries can be scoped to the current user.

### Auth

- `app/main.py` middleware reads `Authorization: Bearer <token>` from headers, looks up `sysUser_{token}` in Redis, extracts the user UUID, and sets it into `ContextVar` (`current_user_uuid`).
- The token is also stored in `auth_token` ContextVar and forwarded to the attend backend API via `app/services/attend_api/base.py`.

### Settings

- `app/core/settings.py` loads from `settings.yml` (YAML) first, then overlays pydantic-settings (which reads `.env`). YAML wins for matching keys.
- Two separate LLM configs: `llm` (main, for function calling and final synthesis) and `text-to-sql-llm` (for SQL generation, typically a faster/cheaper model).
- Database: MySQL via SQLAlchemy with async (`aiomysql`) and sync (`pymysql`) URLs.

### Prompt system

- `app/core/prompts/__init__.py` loads `prompts.md`, injects tool descriptions from `tools/*.md` and examples from `examples/*.md`, then splits into `SYSTEM_PROMPT` and `TOOL_RESULT_PROMPT`.
- `RESULT_SYSTEM_PROMPT` is derived from SYSTEM_PROMPT by stripping the output format section to prevent the LLM from emitting more `TOOL_CALL:` lines during final synthesis.

### Dual chat history

Two history systems coexist:
- **Session-based** (`app/services/agent_service.py`): Messages stored with `session_id` foreign key. Used by `/api/v1/sessions/*` endpoints.
- **User-based** (`app/services/chat_memory.py`): Legacy system storing messages per `user_uuid`. Used when no `session_id` is passed to the chat endpoint.

### Natural language date/time parsing

`app/utils/date_converter.py` and `app/utils/time_converter.py` handle Chinese natural language (今天, 下周一, 5月11日, 下午3点, etc.) with a rule-based parser. Both have `_llm_parse_*` fallbacks that call the LLM when rule parsing fails.
