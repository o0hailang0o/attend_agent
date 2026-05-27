from typing import Sequence
from llama_index.core.tools import FunctionTool

from .daily_attendance import (
    get_employee_attendance,
    get_attendance_summary,
    get_overtime_records,
)
from .apply import register_leave, get_leave_applications
from .leave_balance import get_leave_balance
from .sys_user import search_user
from .door_access import get_door_access
from .approve import approve_list, approve_pass, approve_reject
from .leader import list_leaders
from .dept import list_departments
from .position import list_positions
from .rule import list_rules


def get_available_tools() -> Sequence[FunctionTool]:
    return [
        FunctionTool.from_defaults(fn=get_employee_attendance),
        FunctionTool.from_defaults(fn=get_attendance_summary),
        FunctionTool.from_defaults(fn=get_overtime_records),
        FunctionTool.from_defaults(fn=register_leave),
        FunctionTool.from_defaults(fn=get_leave_applications),
        FunctionTool.from_defaults(fn=get_leave_balance),
        FunctionTool.from_defaults(fn=search_user),
        FunctionTool.from_defaults(fn=get_door_access),
        FunctionTool.from_defaults(fn=approve_list),
        FunctionTool.from_defaults(fn=approve_pass),
        FunctionTool.from_defaults(fn=approve_reject),
        FunctionTool.from_defaults(fn=list_leaders),
        FunctionTool.from_defaults(fn=list_departments),
        FunctionTool.from_defaults(fn=list_positions),
        FunctionTool.from_defaults(fn=list_rules),
    ]