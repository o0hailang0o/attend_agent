import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.sys_user import SysUserController

logger = logging.getLogger(__name__)

def search_user(name: str) -> str:
    """根据姓名模糊搜索员工信息，返回匹配员工列表

    Args:
        name: 搜索关键词。
            - 必填，支持模糊匹配员工姓名（如传入"张"可匹配"张三""张伟"等）
            - 传入空字符串或纯空格时，返回"请输入搜索关键词"提示

    Returns:
        格式化字符串，包含以下信息：
        - 成功时输出格式：
          "我来帮您搜索姓名包含「{name}」的员工。
           找到 N 名包含「{name}」的员工:
           - {姓名}（工号: {workNum}，部门: {deptName}）"
        - 未匹配到时输出格式：
          "我来帮您搜索姓名包含「{name}」的员工。
           未找到姓名包含「{name}」的员工。"
        - 异常时返回："抱歉，搜索员工时系统繁忙，请稍后重试。"

        返回数据字段说明（对接 attend 接口 GET /sysuser，JSON camelCase）：
        - uuid: 业务主键
        - name: 姓名
        - account: 账号
        - nickName: 昵称
        - gender: 性别（1男 0女）
        - workNum: 工号
        - level: 级别
        - position: 职称
        - positionUuid: 职位uuid
        - ruleUuid: 考勤规则uuid
        - ruleName: 考勤规则名称
        - companyId: 公司id
        - deptUuid: 部门uuid
        - deptName: 部门名称
        - createTime: 创建时间
        - updateTime: 修改时间
    """
    logger.info("search_user 传入参数: name=%s", name)
    controller = SysUserController()
    try:
        thinking = f"我来帮您搜索姓名包含「{name}」的员工。"
        logger.info("调用接口 GET /sysuser?name=%s", name)
        result = controller.search_users(name)
        if not result:
            return f"{thinking}\n未找到姓名包含「{name}」的员工。"

        users = result.get('data', []) if isinstance(result, dict) else result
        if not users:
            return f"{thinking}\n未找到姓名包含「{name}」的员工。"

        lines = "\n".join(
            f"- {u.get('name', '未知')}（工号: {u.get('workNum', '未知')}，"
            f"部门: {u.get('deptName', '未知')}，账号: {u.get('account', '未知')}，"
            f"职称: {u.get('position', '未知')}，级别: {u.get('level', '未知')}）"
            for u in users
        )
        return f"{thinking}\n找到 {len(users)} 名包含「{name}」的员工:\n{lines}"
    except Exception as e:
        logger.error("search_user 出错: %s", str(e))
        return "抱歉，搜索员工时系统繁忙，请稍后重试。"

__all__ = ["search_user"]
