import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.rule import RuleController

logger = logging.getLogger(__name__)

def list_rules() -> str:
    """获取考勤规则列表

    调用 attend 接口 GET /rule，返回 Result<List<RuleResp>>。
    RuleResp 字段：
    - id: 主键
    - uuid: 规则uuid
    - name: 规则名称
    - flexibility: 弹性几小时
    - startTime: 上班时间（HH:mm）
    - endTime: 下班时间（HH:mm）
    - middleRest: 中午是否有午休（1是 0否）
    - middleStart: 午休开始时间
    - middleEnd: 午休结束时间
    - vacation: 是否有年假
    - comp: 是否有调休假
    - accuracy: 精确度（0.5或1）
    - overtimeApply: 是否需要加班申请

    Args:
        无参数

    Returns:
        成功时输出格式：
        "我来帮您查询考勤规则。
         共 N 条考勤规则:
         - {name}（上班 {startTime} ~ 下班 {endTime}，弹性 {flexibility}小时）"
        无数据时返回："未找到考勤规则。"
        异常时返回："抱歉，查询考勤规则时系统繁忙，请稍后重试。"
    """
    logger.info("list_rules 被调用")
    controller = RuleController()
    try:
        thinking = "我来帮您查询考勤规则。"
        logger.info("调用接口 GET /rule")
        result = controller.get_attendance_rules()
        data = result.get('data', [])
        if not data:
            return f"{thinking}\n未找到考勤规则。"

        lines = "\n".join(
            f"- {rule.get('name', '未知')}（上班 {rule.get('startTime', '无')} ~ "
            f"下班 {rule.get('endTime', '无')}，弹性 {rule.get('flexibility', 0)}小时）"
            for rule in data
        )
        return f"{thinking}\n共 {len(data)} 条考勤规则:\n{lines}"
    except Exception as e:
        logger.error("list_rules 出错: %s", str(e))
        return "抱歉，查询考勤规则时系统繁忙，请稍后重试。"

__all__ = ["list_rules"]
