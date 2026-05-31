import logging
import time
import traceback
from llama_index.core.llms import ChatMessage, MessageRole
from app.core.llama_index import get_text_to_sql_llm
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

SCHEMA_DESCRIPTION = """
数据库 `attend` 考勤系统表结构：

1. sys_user — 员工信息表
   每行=一个员工。
   uuid（唯一标识）, name（姓名）, account（登录账号/工号，用于精确匹配）, work_num（备用工号），
   dept_uuid → dept.uuid, dept_name（冗余，直接可用）, position_uuid → position.uuid, position（职位名），
   is_delete（1=在职 0=离职）

2. daily_attendance — 每日考勤表
   每行=一个员工某一天的考勤记录。
   employee_uuid → sys_user.uuid, employee_name, date（日期），
   clock_in（上班打卡时间，NULL=未打卡）, clock_out（下班打卡时间，NULL=未打卡），
   actual_work_hours（实际出勤小时）, recognized_hours（系统认定小时），
   leave_hours（请假小时）, annual_leave_hours（年假小时）, comp_leave_hours（调休小时），
   day_type：1=工作日 2=休息日 3=节假日，
   status：1=正常 2=迟到 3=早退 4=缺勤 5=补正，
   is_delete（1=正常）

3. apply — 请假申请表
   每行=一条请假/调休申请。
   apply_user_uuid → sys_user.uuid（谁请的假）, leader_uuid → sys_user.uuid（谁审批），
   type → leave_type.id（请假类型，JOIN leave_type.name 可获中文名），
   month（申请所属月份，如2026-05-01代表5月）,
   start_time（请假开始）, end_time（请假结束）, length（请假小时数），
   reason（请假事由）, reject（驳回时的原因），
   status：1=草稿 2=已通过 3=已撤销 4=待审批 5=审批中 9=未通过，
   is_delete（1=正常）

4. approve — 审批记录表
   每行=一条审批动作。
   apply_uuid → apply.uuid（关联哪条申请）, leader_uuid → sys_user.uuid（审批人），
   `order`（第几级审批，从1开始）, reject（驳回原因），
   status：0=删除 3=驳回 4=待审批 5=审批中 9=审批通过，
   is_delete（1=正常）

5. leave_balance — 假期余额表
   每行=一个员工某一年的假期余额。
   user_uuid → sys_user.uuid, year（年度如2026），
   annual_remaining_hours（剩余年假小时）, comp_remaining_hours（剩余调休小时），
   is_delete（1=正常）

6. leader — 领导/审批链表
   每行=一个领导，定义审批层级关系。
   leader_uuid → sys_user.uuid, leader_name, parent_id（上级领导记录id）, level（级别数字越小越高），
   tree（审批链文本，如"总经理→部门经理"）

7. dept — 部门表
   uuid, name（部门名称）, parent_uuid（上级部门uuid，NULL=顶级部门）,
   manager_uuid → sys_user.uuid（部门负责人）, is_delete（1=正常）

8. position — 职位表
   uuid, name（职位名称）, is_delete（1=正常）

9. rule — 考勤规则表
   每行=一套考勤规则（弹性、午休、加班等）。
   uuid, name, start_time（规定上班时间）, end_time（规定下班时间），
   flexibility（允许弹性分钟数）, middle_rest（午休是否计工时0/1）,
   middle_start（午休开始）, middle_end（午休结束），
   overtime_apply（加班是否需要申请0/1），
   is_delete（1=正常）

10. door_access — 门禁打卡记录表
    每行=一次刷卡进出记录。
    employee_uuid → sys_user.uuid, employee_name, work_num, door_no（门禁点编号），
    direction：0=进门 1=出门, access_datetime（刷卡时间），
    is_delete（1=正常）

11. leave_type — 假期类型表
    uuid, name（类型名如：年假、事假、病假、调休）, deduct_balance（1=扣余额 0=不扣），
    is_delete（1=正常）

表关联速查：
- 员工考勤：daily_attendance.employee_uuid = sys_user.uuid
- 请假申请：apply.apply_user_uuid = sys_user.uuid, apply.type = leave_type.id
- 审批记录：approve.apply_uuid = apply.uuid, approve.leader_uuid = sys_user.uuid
- 假期余额：leave_balance.user_uuid = sys_user.uuid
- 领导链：leader.leader_uuid = sys_user.uuid
- 部门：dept.uuid = sys_user.dept_uuid, dept.parent_uuid = dept.uuid（自关联）
"""

SQL_GENERATION_PROMPT = """你是考勤系统的 SQL 专家。根据以上数据库表结构，将用户问题转换为 MySQL 查询。

重要：你只能生成 SELECT 查询，不允许任何写操作。
如果用户问题符合以下任一情况，直接输出 SKIP：
- 涉及请假申请、审批、提交、修改、删除等写操作
- 与考勤数据完全无关（如：今天几号、今天星期几、天气、闲聊、你是谁等）
- 是纯日期/时间询问，不涉及任何考勤业务数据
- 无法从上述数据库表中查到答案

要求：
1. 只输出一条 SELECT 语句，不要输出任何其他内容
2. 使用 WHERE is_delete = 1 过滤已删除的数据
3. 结果按时间倒序排列（如果涉及日期）
4. 限制结果最多 20 条
5. 用中文别名(AS)让输出易于理解

用户问题：{query}
SQL："""


def _execute_sql(sql: str) -> str:
    """执行 SQL 并返回格式化结果"""
    if not sql:
        return ""
    try:
        from sqlalchemy import text

        session = SessionLocal()
        try:
            rows = session.execute(text(sql)).fetchmany(20)
            if not rows:
                return "查询结果为空"

            col_names = list(rows[0]._fields) if hasattr(rows[0], '_fields') else [f"col{i}" for i in range(len(rows[0]))]
            lines = [" | ".join(col_names)]
            lines.append("-|-".join(["---"] * len(col_names)))
            for row in rows:
                vals = [str(v) if v is not None else "NULL" for v in row]
                lines.append(" | ".join(vals))
            return "\n".join(lines)
        finally:
            session.close()
    except Exception as e:
        logger.warning("SQL 执行失败: %s\nSQL: %s", str(e), sql)
        import traceback
        logger.warning(traceback.format_exc())
        return "查询结果为空"


def text_to_sql(query: str, user_uuid: str = None) -> str:
    """执行 text-to-sql 流程：LLM 生成 SQL → 执行 → 返回结果"""
    logger.info("text_to_sql 开始处理: query=%s, user_uuid=%s", query, user_uuid[:8] if user_uuid else None)
    try:
        llm = get_text_to_sql_llm()
        prompt = SQL_GENERATION_PROMPT.format(query=query)
        if user_uuid:
            prompt += (
                f"\n当前登录用户的 UUID 是 '{user_uuid}'。"
                "如果查询涉及当前用户自己的数据，请直接在 WHERE 条件中使用这个 UUID 值，"
                f"例如 WHERE employee_uuid = '{user_uuid}' 或 WHERE apply_user_uuid = '{user_uuid}'。"
                "不要使用 current_user 这种不存在的表名。"
            )
        msg = ChatMessage(role=MessageRole.USER, content=SCHEMA_DESCRIPTION + "\n\n" + prompt)

        sql = ""
        for attempt in range(3):
            try:
                r = llm.chat(messages=[msg])
                sql = (r.message.content or "").strip()
                sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate limit" in err_str.lower():
                    wait = 3 * (attempt + 1)
                    logger.warning("text_to_sql 速率限制（第 %d 次），等待 %ds 后重试", attempt + 1, wait)
                    time.sleep(wait)
                else:
                    logger.warning("text_to_sql LLM 调用失败: %s", err_str)
                    break

        logger.info("生成的 SQL: %s", sql)
        if not sql or sql.upper().strip() == "SKIP":
            logger.info("text_to_sql 跳过（写操作或无 SQL）")
            return ""
        if not sql.upper().strip().startswith("SELECT"):
            logger.warning("text_to_sql 拒绝执行非 SELECT 语句: %s", sql[:100])
            return ""
        result = _execute_sql(sql)
        if not result or result == "查询结果为空":
            logger.info("text_to_sql SQL 执行无结果，跳过")
            return ""
        logger.info("text_to_sql 完成，返回 %d 字符", len(result))
        return result
    except Exception as e:
        logger.warning("text_to_sql 整体异常: %s", str(e))
        return ""


    