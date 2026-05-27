from pathlib import Path


def _load_md_dir(dirname: str) -> str:
    d = Path(__file__).parent / dirname
    parts = []
    for f in sorted(d.glob("*.md")):
        content = f.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)
    return "\n\n".join(parts)


def _load_prompts() -> tuple[str, str]:
    md_path = Path(__file__).parent / "prompts.md"
    content = md_path.read_text(encoding="utf-8")
    content = content.replace("{tools}", _load_md_dir("tools"))
    content = content.replace("{examples}", _load_md_dir("examples"))

    parts = content.split("\n# ")
    system = ""
    tool_result = ""
    for part in parts:
        key = part.split("\n", 1)[0].strip()
        val = part.split("\n", 1)[1].strip() if "\n" in part else ""
        if key == "# SYSTEM_PROMPT" or key == "SYSTEM_PROMPT":
            system = val
        elif key == "# TOOL_RESULT_PROMPT" or key == "TOOL_RESULT_PROMPT":
            tool_result = val
    return system, tool_result


SYSTEM_PROMPT, TOOL_RESULT_PROMPT = _load_prompts()

# 工具结果阶段的 system prompt：不含 TOOL_CALL 输出格式，防止 LLM 二次输出
_RESULT_HEAD = SYSTEM_PROMPT.split("## 输出格式")[0].rstrip()
RESULT_SYSTEM_PROMPT = _RESULT_HEAD + "\n\n请根据用户问题和工具执行结果，用中文自然地回答用户。不要输出 TOOL_CALL: 行。"
