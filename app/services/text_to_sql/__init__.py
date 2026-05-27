import logging
import time
import traceback
from llama_index.core.llms import ChatMessage, MessageRole
from app.core.llama_index import get_text_to_sql_llm
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

SCHEMA_DESCRIPTION = """
数据库 `attend` 中的核心表结构：

1. sys_user — 系统用户
   uuid, name, account(工号), work_num(备用工号), dept_uuid（部门uuid 与 dept表的uuid相关联）, dept_name（部门名称）, position, is_delete(1=正常,0=删除)

2. daily_attendance — 每日考勤统计
   uuid, employee_uuid, employee_name, date(日期), clock_in(上班时间), clock_out(下班时间),
   actual_work_hours(实际工时), recognized_hours(认定工时), leave_hours(请假小时),
   annual_leave_hours(年假小时), comp_leave_hours(调休假小时),
   day_type(1工作日 2休息日 3假日), status(1正常 2迟到 3早退 4缺勤 5补正),
   is_delete(1=正常,0=删除)

3. apply — 考勤申请(请假单)
   uuid, month(月份), type(申请类型), start_time(开始时间), end_time(结束时间),
   length(时长), apply_user_uuid(申请人), leader_uuid(审批人), reason(事由),
   status(1提交 4审批中 2通过 3撤销 9未通过), is_delete(1=正常,0=删除)

4. approve — 审批
   uuid, apply_uuid(申请uuid), `order`(审批顺序), leader_uuid(审批人),
   reject(驳回原因), status(0删除 3驳回 4待审批 5审批中 9审批完成)

5. leave_balance — 假期余额
   uuid, user_uuid(员工uuid  关联 sys_user字段uuid), year(年度), annual_remaining_hours(年假剩余小时), comp_remaining_hours(调休假剩余小时)

6. leader — 公司领导审批链
   leader_uuid(领导用户uuid 关联 sys_user表的uuid字段), leader_name(姓名), level(级别)

7. dept — 部门
   uuid, name(部门名称), parent_uuid(上级部门)

8. `position` — 职位
   uuid, name(职位名称)

9. rule — 考勤规则
   uuid, name(规则名称), start_time(上班时间), end_time(下班时间)

10. door_access — 门禁开门记录, 打卡记录
    uuid（主键uuid）, employee_uuid（员工uuid 关联 sys_user表的 uuid）, employee_name（员工姓名）, work_num(工号), door_no(门号),
    direction(0进 1出), access_time(通行时间), access_date(通行日期)

11. leave_type — 假期类型
    uuid（逐渐uuid）, name(假期类型名称), deduct_balance(是否扣减余额)

注意：
- 所有表都有 is_delete 字段，查询时默认过滤 is_delete = 1
- 日期字段为 DATE 或 TIMESTAMP 类型
- 请假类型 type 对应 leave_type 中的类型编码
- sys_user 中 account(工号) 和 work_num(备用工号) 都可能用于员工识别
"""

SQL_GENERATION_PROMPT = """你是考勤系统的 SQL 专家。根据以上数据库表结构，将用户问题转换为 MySQL 查询。

要求：
1. 只输出一条 SQL，不要输出任何其他内容
2. 使用 WHERE is_delete = 1 过滤已删除的数据
3. 结果按时间倒序排列（如果涉及日期）
4. 限制结果最多 20 条
5. 用中文别名(AS)让输出易于理解

用户问题：{query}
SQL："""


def _generate_sql(query: str) -> str:
    """使用 LLM 将自然语言转为 SQL（含重试）"""
    llm = get_text_to_sql_llm()
    prompt = SQL_GENERATION_PROMPT.format(query=query)
    msg = ChatMessage(role=MessageRole.USER, content=SCHEMA_DESCRIPTION + "\n\n" + prompt)

    # 错峰启动，降低与主 LLM 同时调用的速率限制冲突
    time.sleep(1.5)

    for attempt in range(1):
        try:
            r = llm.chat(messages=[msg])
            sql = (r.message.content or "").strip()
            sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
            logger.info("生成的 SQL: %s", sql)
            return sql
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate limit" in err_str.lower():
                wait = 3 * (attempt + 1)
                logger.warning("速率限制（第 %d 次），等待 %ds 后重试", attempt + 1, wait)
                time.sleep(wait)
                continue
            logger.warning("SQL 生成失败: %s", err_str)
            break
    return ""


def _execute_sql(sql: str) -> str:
    """执行 SQL 并返回格式化结果"""
    if not sql:
        return ""
    try:
        session = SessionLocal()
        try:
            rows = session.execute(sql).fetchmany(20)
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
        return f"SQL 执行出错: {e}"


def text_to_sql(query: str, user_uuid: str = None) -> str:
    """执行 text-to-sql 流程：LLM 生成 SQL → 执行 → 返回结果"""
    logger.info("text_to_sql 开始处理: query=%s, user_uuid=%s", query, user_uuid[:8] if user_uuid else None)
    try:
        llm = get_text_to_sql_llm()
        prompt = SQL_GENERATION_PROMPT.format(query=query)
        if user_uuid:
            prompt += f"\n当前用户的 UUID 是 {user_uuid}。请在 SQL 中使用此 UUID 过滤相关记录。"
        msg = ChatMessage(role=MessageRole.USER, content=SCHEMA_DESCRIPTION + "\n\n" + prompt)
        r = llm.chat(messages=[msg])
        sql = (r.message.content or "").strip()
        sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
        logger.info("生成的 SQL: %s", sql)
        if not sql:
            logger.info("text_to_sql 未生成 SQL，跳过")
            return ""
        result = _execute_sql(sql)
        if not result:
            logger.info("text_to_sql SQL 执行无结果，跳过")
            return ""
        logger.info("text_to_sql 完成，返回 %d 字符", len(result))
        return f"【数据库查询结果】\nSQL: {sql}\n\n{result}"
    except Exception as e:
        logger.warning("text_to_sql 整体异常: %s", str(e))
        return ""

if __name__ == '__main__':
    sql = _generate_sql("最后一次打卡")
    print(sql)
    