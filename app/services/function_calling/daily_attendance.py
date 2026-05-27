import logging
from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.daily_attendance import DailyAttendanceController
from app.utils.user_lookup import resolve_user
from app.utils.date_converter import DateConverter

logger = logging.getLogger(__name__)

def get_employee_attendance(employee_identifier: str, date: str) -> str:
    """查询单个员工某天的考勤记录（上班时间、下班时间、实际工时、考勤状态等）

    调用 attend 接口 GET /dailyAttendance?employeeUuid={uuid}&date={date}，
    返回 Result<List<DailyAttendanceResp>>。

    Args:
        employee_identifier: 员工姓名或工号。传空字符串时查当前登录用户
        date: 日期，支持自然语言（今天、昨天、周一、5月11日等）

    Returns:
        成功时输出格式：
        "我来帮您查询{name}在{date}的考勤记录。
         员工: {employeeName}
         日期: {date}
         上班: {clockIn}
         下班: {clockOut}
         实际工时: {actualWorkHours}小时
         考勤状态: {statusName}
         日类型: {dayTypeName}"
        未找到记录时返回："{name}在{date}没有考勤记录。"
        异常时返回："抱歉，查询考勤记录时系统繁忙，请稍后重试。"
    """
    logger.info("get_employee_attendance 传入参数: employee_identifier=%s, date=%s", employee_identifier, date)
    controller = DailyAttendanceController()
    try:
        uuid = resolve_user(employee_identifier)
        logger.info("员工解析结果: %s -> %s", employee_identifier, uuid)
        if not uuid:
            return f"未找到员工「{employee_identifier}」，请确认姓名或工号是否正确。"
        parsed = DateConverter.parse_date_to_string(date)
        date_str = parsed if parsed else date
        logger.info("日期解析结果: %s -> %s", date, date_str)
        logger.info("调用接口 GET /dailyAttendance?employeeUuid=%s&date=%s", uuid, date_str)
        result = controller.get_employee_attendance(uuid, date_str)
        data = result.get('data', [])
        if not data:
            return f"我来帮您查询{employee_identifier}在{date_str}的考勤记录。\n{employee_identifier}在{date_str}没有考勤记录。"

        record = data[0] if isinstance(data, list) else data
        employee_name = record.get('employeeName', employee_identifier)
        clock_in = record.get('clockIn', '无')
        clock_out = record.get('clockOut', '无')
        hours = record.get('actualWorkHours', '无')
        status_name = record.get('statusName', '未知')
        day_type_name = record.get('dayTypeName', '未知')
        return (
            f"我来帮您查询{employee_identifier}在{date_str}的考勤记录。\n"
            f"员工: {employee_name}\n"
            f"日期: {date_str}\n"
            f"上班: {clock_in}\n"
            f"下班: {clock_out}\n"
            f"实际工时: {hours}小时\n"
            f"考勤状态: {status_name}\n"
            f"日类型: {day_type_name}"
        )
    except Exception as e:
        logger.error("get_employee_attendance 出错: %s", str(e))
        return "抱歉，查询考勤记录时系统繁忙，请稍后重试。"

def get_attendance_summary(date: str) -> str:
    """查询某天全体出勤汇总（出勤率、迟到、缺勤等统计）

    调用 attend 接口 GET /dailyAttendance?date={date}，
    返回 Result<List<DailyAttendanceResp>>，按 statusName 字段聚合统计。

    Args:
        date: 日期，支持自然语言（今天、昨天、周一、5月11日等）

    Returns:
        成功时输出格式：
        "我来帮您查询{date}的考勤汇总。
         {date}考勤汇总（共 N 人）:
         - 正常: N 人
         - 迟到: N 人
         - 早退: N 人
         - 缺勤: N 人
         - 补正: N 人"
        异常时返回："抱歉，查询考勤汇总时系统繁忙，请稍后重试。"

        后端 DailyAttendanceResp.statusName 取值：正常/迟到/早退/缺勤/补正
    """
    logger.info("get_attendance_summary 传入参数: date=%s", date)
    controller = DailyAttendanceController()
    try:
        parsed = DateConverter.parse_date_to_string(date)
        date_str = parsed if parsed else date
        logger.info("日期解析结果: %s -> %s", date, date_str)
        logger.info("调用接口 GET /dailyAttendance?date=%s", date_str)
        result = controller.get_attendance_summary(date_str)
        data = result.get('data', [])
        if not data:
            return f"我来帮您查询{date_str}的考勤汇总。\n{date_str}没有考勤数据。"

        total = len(data)
        stats = {}
        for r in data:
            s = r.get('statusName', '未知')
            stats[s] = stats.get(s, 0) + 1

        lines = "\n".join(f"- {k}: {v}人" for k, v in sorted(stats.items()))
        return f"我来帮您查询{date_str}的考勤汇总。\n{date_str}考勤汇总（共 {total} 人）:\n{lines}"
    except Exception as e:
        logger.error("get_attendance_summary 出错: %s", str(e))
        return "抱歉，查询考勤汇总时系统繁忙，请稍后重试。"

def get_overtime_records(employee_identifier: str, start_date: str, end_date: str) -> str:
    """查询员工在日期范围内的加班记录（实际工时 > 8 小时）

    调用 attend 接口 GET /dailyAttendance?employeeUuid={uuid}&startDate={s}&endDate={e}，
    返回 Result<List<DailyAttendanceResp>>，本地过滤 actualWorkHours > 8 的记录。

    Args:
        employee_identifier: 员工姓名或工号。传空字符串时查当前登录用户
        start_date: 开始日期，支持自然语言
        end_date: 结束日期，支持自然语言

    Returns:
        成功时输出格式：
        "我来帮您查询{name}在{start}至{end}期间的加班记录。
         找到 N 条加班记录:
         - {date}: 实际工时 {actualWorkHours}小时（上班 {clockIn} ~ 下班 {clockOut}）"
        无记录时返回："{name}在{start}至{end}期间没有加班记录。"
        异常时返回："抱歉，查询加班记录时系统繁忙，请稍后重试。"
    """
    logger.info("get_overtime_records 传入参数: employee_identifier=%s, start_date=%s, end_date=%s",
                employee_identifier, start_date, end_date)
    controller = DailyAttendanceController()
    try:
        uuid = resolve_user(employee_identifier)
        logger.info("员工解析结果: %s -> %s", employee_identifier, uuid)
        if not uuid:
            return f"未找到员工「{employee_identifier}」，请确认姓名或工号是否正确。"
        s_parsed = DateConverter.parse_date_to_string(start_date)
        e_parsed = DateConverter.parse_date_to_string(end_date)
        start_str = s_parsed if s_parsed else start_date
        end_str = e_parsed if e_parsed else end_date
        logger.info("日期解析结果: %s -> %s, %s -> %s", start_date, start_str, end_date, end_str)
        logger.info("调用接口 GET /dailyAttendance?employeeUuid=%s&startDate=%s&endDate=%s", uuid, start_str, end_str)
        result = controller.get_overtime_records(uuid, start_str, end_str)
        data = result.get('data', [])
        overtime = [r for r in data if r.get('actualWorkHours', 0) and float(str(r.get('actualWorkHours', 0))) > 8]

        if not overtime:
            return f"我来帮您查询{employee_identifier}在{start_str}至{end_str}期间的加班记录。\n{employee_identifier}在{start_str}至{end_str}期间没有加班记录。"

        lines = "\n".join(
            f"- {r.get('date', '未知')}: 实际工时 {r.get('actualWorkHours', 0)}小时"
            f"（上班 {r.get('clockIn', '无')} ~ 下班 {r.get('clockOut', '无')}）"
            for r in overtime
        )
        return f"我来帮您查询{employee_identifier}在{start_str}至{end_str}期间的加班记录。\n找到 {len(overtime)} 条加班记录:\n{lines}"

    except Exception as e:
        logger.error("get_overtime_records 出错: %s", str(e))
        return "抱歉，查询加班记录时系统繁忙，请稍后重试。"

__all__ = ["get_employee_attendance", "get_attendance_summary", "get_overtime_records"]
