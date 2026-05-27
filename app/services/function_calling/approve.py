import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.approve import ApproveController
from app.utils.user_lookup import resolve_user

logger = logging.getLogger(__name__)

def approve_list(employee_identifier: str = "") -> str:
    """获取待审批列表

    调用 attend 接口 GET /approve/my，返回 Result<IPage<ApproveApplyResp>>（分页）。
    ApproveApplyResp 字段：
    - approveUuid: 审批uuid
    - applyUuid: 申请uuid
    - order: 审批顺序
    - approveStatus: 审批状态（0删除 3驳回 4待审批 5审批中 1通过 9审批通过）
    - approveStatusName: 审批状态名称
    - type: 申请类型
    - lengthType: 请假时间类型
    - startTime: 开始时间
    - endTime: 结束时间
    - length: 时长
    - reason: 请假事由
    - applyUserName: 申请人姓名
    - applyUserWorkNum: 申请人工号
    - reject: 驳回原因
    - createTime: 创建时间

    Args:
        employee_identifier: 员工姓名或工号。当前未使用（接口固定查当前用户的审批列表），
                             传空字符串即可

    Returns:
        成功时输出格式：
        "我来帮您查询待审批列表。
         待审批列表（共 N 条）:
         - {applyUserName} | {type} | {startTime}~{endTime} | {approveStatusName}"
        无待审批时返回："目前没有待审批的申请。"
        异常时返回："抱歉，查询待审批列表时系统繁忙，请稍后重试。"
    """
    logger.info("approve_list 传入参数: employee_identifier=%s", employee_identifier)
    controller = ApproveController()
    try:
        thinking = "我来帮您查询待审批列表。"
        logger.info("调用接口 GET /approve/my")
        result = controller.get_approval_list()
        raw = result.get('data', {})
        records = raw.get('records', []) if isinstance(raw, dict) else raw

        if not records:
            return f"{thinking}\n目前没有待审批的申请。"

        lines = "\n".join(
            f"- {r.get('applyUserName', '未知')} | {r.get('type', '未知')} "
            f"| {r.get('startTime', '未知')}~{r.get('endTime', '未知')} "
            f"| {r.get('approveStatusName', '未知')}"
            for r in records
        )
        return f"{thinking}\n待审批列表（共 {len(records)} 条）:\n{lines}"
    except Exception as e:
        logger.error("approve_list 出错: %s", str(e))
        return "抱歉，查询待审批列表时系统繁忙，请稍后重试。"

def approve_pass(approve_uuid: str) -> str:
    """审批通过

    调用 attend 接口 PUT /approve/pass，请求体 {"uuid": "{approve_uuid}"}。

    Args:
        approve_uuid: 审批 uuid（来自 approve_list 返回的 approveUuid）

    Returns:
        成功时返回："审批已通过。"
        异常时返回："抱歉，审批通过时系统繁忙，请稍后重试。"
    """
    logger.info("approve_pass 传入参数: approve_uuid=%s", approve_uuid)
    controller = ApproveController()
    try:
        logger.info("调用接口 PUT /approve/pass uuid=%s", approve_uuid)
        controller.approve_pass(approve_uuid)
        return "审批已通过。"
    except Exception as e:
        logger.error("approve_pass 出错: %s", str(e))
        return "抱歉，审批通过时系统繁忙，请稍后重试。"

def approve_reject(approve_uuid: str, reason: str) -> str:
    """审批驳回

    调用 attend 接口 PUT /approve/reject，请求体 {"uuid": "{approve_uuid}", "reject": "{reason}"}。

    Args:
        approve_uuid: 审批 uuid（来自 approve_list 返回的 approveUuid）
        reason: 驳回原因

    Returns:
        成功时返回："审批已驳回，原因: {reason}"
        异常时返回："抱歉，审批驳回时系统繁忙，请稍后重试。"
    """
    logger.info("approve_reject 传入参数: approve_uuid=%s, reason=%s", approve_uuid, reason)
    controller = ApproveController()
    try:
        logger.info("调用接口 PUT /approve/reject uuid=%s reject=%s", approve_uuid, reason)
        controller.approve_reject(approve_uuid, reason)
        return f"审批已驳回，原因: {reason}"
    except Exception as e:
        logger.error("approve_reject 出错: %s", str(e))
        return "抱歉，审批驳回时系统繁忙，请稍后重试。"

__all__ = ["approve_list", "approve_pass", "approve_reject"]
