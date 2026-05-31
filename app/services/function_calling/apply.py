import logging
from llama_index.core.tools import FunctionTool
from app.services.attend_api.apply import ApplyController, map_leave_type
from app.utils.user_lookup import resolve_user
from app.utils.time_converter import TimeConverter
from app.utils.attend_code_converter import LeaveTypeConverter

logger = logging.getLogger(__name__)


def register_leave(
    employee_identifier: str = "",
    leave_type: str = "",
    range: str = "",
    reason: str = "",
    leader: str = "",
    confirmed: bool = False,
) -> str:
    """提交请假申请（多轮对话，参数可分批传入）

    这是一个多轮对话工具。用户可能分多次提供参数，每次调用此函数都会检查参数是否齐全：
    1. 参数不全 → 返回提示，告诉用户还缺什么
    2. 参数齐全且 confirmed=False → 展示请假单摘要，让用户确认
    3. 参数齐全且 confirmed=True → 正式提交到 attend 系统

    必填参数:
    - leave_type: 请假类型（年假/事假/病假/婚假/产假/丧假/调休）
    - range: 请假时间范围（自然语言，如"下周一上午9点到下午5点"）
    - reason: 请假原因
    - leader: 审批人姓名或工号

    Args:
        employee_identifier: 员工姓名或工号（空字符串表示当前登录用户）
        leave_type: 请假类型
        range: 请假时间范围，支持自然语言
        reason: 请假原因
        leader: 审批人姓名或工号
        confirmed: 是否确认提交（用户确认后传 True）

    Returns:
        参数不全时：提示缺少哪些参数
        未确认时：展示请假单摘要，提示用户确认
        已确认时：提交成功或失败信息

    重要：当用户补充了缺失的参数（如审批人 leader）时，必须再次调用本工具重新提交所有参数，
    将用户新提供的参数值填入，同时保留之前已知的所有参数。不要直接回答用户。
    """
    logger.info("register_leave 传入参数: employee_identifier=%s, leave_type=%s, range=%s, reason=%s, leader=%s, confirmed=%s",
                employee_identifier, leave_type, range, reason, leader, confirmed)

    # 检查必填参数
    missing = []
    if not leave_type:
        missing.append("请假类型（年假/事假/病假/婚假/产假/丧假/调休）")
    if not range:
        missing.append("请假时间范围（如下周一 上午9点到下午5点）")
    if not reason:
        missing.append("请假原因")
    if not leader:
        missing.append("审批人")

    if missing:
        return (
            f"还需要提供以下信息：\n" + "\n".join(f"- {m}" for m in missing)
            + "\n\n【系统指令】接下来用户会提供缺失的信息。当用户提供了某项缺失信息后，你必须立即再次调用 register_leave，"
            "把之前已经传入的参数和用户新提供的参数合并后一起传进来。"
            "严禁使用你的内部知识回答用户关于人名、地名等问题。"
        )

    # 解析时间范围
    
    start_str, end_str = TimeConverter.parse_natural_range(range)
    if not start_str:
        return f"未能解析请假时间「{range}」，请重新描述（如下周一 上午9点到下午5点）。"
    if not end_str:
        return f"请假时间「{range}」缺少结束时间，请同时提供开始和结束时间（如下周一 上午9点到下午5点）。"
    # 未确认 → 展示摘要
    if not confirmed:
        return (
            f"请假单确认：\n"
            f"  申请人：{'当前用户' if not employee_identifier else employee_identifier}\n"
            f"  请假类型：{leave_type}\n"
            f"  开始时间：{start_str}\n"
            f"  结束时间：{end_str}\n"
            f"  请假原因：{reason}\n"
            f"  审批人：{leader}\n\n"
            f"请确认是否提交？（回复 确认 或 提交）"
        )

    # 已确认 → 正式提交
    controller = ApplyController()
    try:
        uuid = resolve_user(employee_identifier)
        if not uuid:
            return "未找到当前用户信息，请重新登录后重试。"
        type_code = map_leave_type(leave_type)
        month = start_str[:7] + "-01"
        data = {
            "type": type_code,
            "month": month,
            "startTime": start_str,
            "endTime": end_str,
            "reason": reason,
            "applyUserUuid": uuid,
        }
        if leader:
            leader_uuid = resolve_user(leader)
            if leader_uuid:
                data["leaderUuid"] = leader_uuid
        logger.info("调用接口 POST /apply data=%s", data)
        result = controller.submit_leave_application(data)
        if result.get("code") != 200:
            msg = result.get("msg", "未知错误")
            logger.warning("提交请假申请失败: code=%s, msg=%s", result.get("code"), msg)
            return f"请假申请提交失败：{msg}，请稍后重试或联系管理员。"
        return f"请假申请已提交成功！n{leave_type} | {start_str} ~ {end_str} | {reason}"
    except Exception as e:
        logger.error("register_leave 出错: %s", str(e))
        return "抱歉，提交请假申请时系统繁忙，请稍后重试。"


def get_leave_applications(employee_identifier: str = "") -> str:
    """获取请假申请列表

    调用 attend 接口 GET /apply?userUuid={uuid}，返回 Result<IPage<ApplyResp>>。
    ApplyResp 字段（JSON camelCase）：
    - uuid: 申请uuid
    - type: 申请类型（Integer，对应 LeaveType.id）
    - lengthType: 请假时间类型
    - startTime: 开始时间
    - endTime: 结束时间
    - length: 时长
    - reason: 请假事由
    - applyUserUuid: 申请人uuid
    - leaderUuid: 审批人uuid
    - reject: 驳回原因
    - status: 状态（1提交 2保存 3驳回 4待审批 5审批中 9审批通过）
    - statusName: 状态名称
    - createTime: 创建时间
    - updateTime: 修改时间

    Args:
        employee_identifier: 员工姓名或工号。传空字符串时查当前用户；传具体姓名/工号时查该员工

    Returns:
        成功时输出格式：
        "共 N 条请假申请：
         - {startTime}~{endTime} | {type} | {statusName} | {reason}"
        无记录时返回："暂无请假申请记录。"
        异常时返回："抱歉，查询请假申请时系统繁忙，请稍后重试。"
    """
    controller = ApplyController()
    try:
        uuid = resolve_user(employee_identifier) if employee_identifier else None
        result = controller.get_leave_applications(user_uuid=uuid)
        raw = result.get('data', {})
        records = raw.get('records', []) if isinstance(raw, dict) else raw
        if not records:
            return "暂无请假申请记录。"
        lines = [f"共 {len(records)} 条请假申请："]
        for app in records:
            st = app.get('startTime', '未知')
            et = app.get('endTime', '未知')
            tp = LeaveTypeConverter.to_name(app.get('type', 0))
            sts = app.get('statusName', '未知')
            rsn = app.get('reason', '')
            rsn_part = f"（{rsn}）" if rsn else ""
            lines.append(f"- {st}~{et} | {tp} | {sts}{rsn_part}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("get_leave_applications 出错: %s", str(e))
        return "抱歉，查询请假申请时系统繁忙，请稍后重试。"
