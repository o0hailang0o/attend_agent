from typing import Sequence

from llama_index.core.tools import FunctionTool


def get_employee_attendance(employee_id: str, date: str) -> str:
    """获取员工某天的考勤记录

    Args:
        employee_id: 员工编号
        date: 日期，格式 YYYY-MM-DD
    """
    return f"Employee {employee_id} attendance on {date}: present"


def get_attendance_summary(date: str, department: str = "") -> str:
    """获取某天的考勤汇总

    Args:
        date: 日期，格式 YYYY-MM-DD
        department: 部门名称（可选）
    """
    dept = department or "all"
    return f"Attendance summary for {dept} on {date}: 100% attendance"


def get_overtime_records(employee_id: str, start_date: str, end_date: str) -> str:
    """获取员工在日期范围内的加班记录

    Args:
        employee_id: 员工编号
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
    """
    return (
        f"Overtime records for {employee_id} "
        f"from {start_date} to {end_date}: 0 hours"
    )


def register_leave(
    employee_id: str, leave_type: str, start_date: str, end_date: str
) -> str:
    """为员工登记请假

    Args:
        employee_id: 员工编号
        leave_type: 请假类型（annual/sick/personal）
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
    """
    return (
        f"Leave registered: {employee_id} - {leave_type} "
        f"from {start_date} to {end_date}"
    )


def get_available_tools() -> Sequence[FunctionTool]:
    return [
        FunctionTool.from_defaults(fn=get_employee_attendance),
        FunctionTool.from_defaults(fn=get_attendance_summary),
        FunctionTool.from_defaults(fn=get_overtime_records),
        FunctionTool.from_defaults(fn=register_leave),
    ]
