from typing import List, Optional
from llama_index.core.tools import FunctionTool
from app.services.attend_api.daily_attendance import DailyAttendanceController

def get_employee_attendance(employee_identifier: str, date: str) -> str:
    """获取员工某日的考勤记录"""
    controller = DailyAttendanceController()
    try:
        # 这里需要将employee_identifier转换为employee_uuid
        # 简化处理，假设employee_identifier就是employee_uuid
        result = controller.get_employee_attendance(employee_identifier, date)
        data = result.get('data', {})
        return f"员工 {employee_identifier} 在 {date} 的考勤记录: {data.get('status', '未知')}"
    except Exception as e:
        return f"获取考勤记录时出错: {str(e)}"

def get_attendance_summary(date: str) -> str:
    """获取某日考勤汇总"""
    controller = DailyAttendanceController()
    try:
        result = controller.get_attendance_summary(date)
        data = result.get('data', {})
        return f"{date} 考勤汇总: {data.get('summary', '无数据')}"
    except Exception as e:
        return f"获取考勤汇总时出错: {str(e)}"

def get_overtime_records(employee_identifier: str, start_date: str, end_date: str) -> str:
    """获取员工在日期范围内的加班记录"""
    controller = DailyAttendanceController()
    try:
        # 简化处理，假设employee_identifier就是employee_uuid
        result = controller.get_overtime_records(employee_identifier, start_date, end_date)
        data = result.get('data', [])
        if not data:
            return f"员工 {employee_identifier} 在 {start_date} 到 {end_date} 期间没有加班记录"
        
        response = f"员工 {employee_identifier} 在 {start_date} 到 {end_date} 期间的加班记录:\n"
        for record in data:
            response += f"- {record.get('date', '未知')}: 加班 {record.get('overtime_hours', 0)} 小时\n"
        
        return response
    except Exception as e:
        return f"获取加班记录时出错: {str(e)}"

__all__ = ["get_employee_attendance", "get_attendance_summary", "get_overtime_records"]