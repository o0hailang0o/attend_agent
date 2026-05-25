from datetime import datetime, timedelta
import re
from typing import Union, Optional
import zhconv

class DateConverter:
    """日期转换工具，支持自然语言日期描述转换为实际日期"""
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        解析自然语言日期描述为datetime对象
        
        支持的格式：
        - 今天、昨天、明天、后天、大后天、大前天
        - 星期一、这周一、上周一、上个星期一
        - 上个月、下个月
        - 去年、今年、明年
        - 具体日期格式：2023-01-01、01/01/2023、2023年1月1日等
        
        Args:
            date_str: 自然语言日期描述
            
        Returns:
            datetime对象或None（如果无法解析）
        """
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        # 处理简体中文字符
        if any(c in date_str for c in ['昨', '今', '明', '后', '前', '星', '月', '年']):
            date_str = zhconv.convert(date_str, 'zh-cn')
        
        now = datetime.now()
        
        # 处理相对日期
        if date_str == "今天":
            return now
        elif date_str == "昨天":
            return now - timedelta(days=1)
        elif date_str == "明天":
            return now + timedelta(days=1)
        elif date_str == "后天":
            return now + timedelta(days=2)
        elif date_str == "大后天":
            return now + timedelta(days=3)
        elif date_str == "大前天":
            return now - timedelta(days=3)
        
        # 处理星期
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        if date_str in weekdays or date_str in weekday_names:
            target_weekday = weekdays.index(date_str) if date_str in weekdays else weekday_names.index(date_str)
            current_weekday = now.weekday()
            days_diff = target_weekday - current_weekday
            if days_diff < 0:
                days_diff += 7
            return now + timedelta(days=days_diff)
        
        # 处理"这周一"、"本周一"
        if re.match(r"这(?:周|星)一|本周一", date_str):
            monday = now - timedelta(days=now.weekday())
            return monday
        
        # 处理"上周一"、"上星期一"
        if re.match(r"上(?:周|星)一|上周一|上星期一", date_str):
            monday = now - timedelta(days=now.weekday() + 7)
            return monday
        
        # 处理"上个星期一"
        if re.match(r"上个星期一", date_str):
            monday = now - timedelta(days=now.weekday() + 14)
            return monday
        
        # 处理月份
        if date_str == "上个月":
            return now.replace(day=1) - timedelta(days=1)
        elif date_str == "下个月":
            next_month = now.month % 12 + 1
            year = now.year + (now.month // 12)
            return datetime(year, next_month, 1)
        
        # 处理年份
        if date_str == "去年":
            return now.replace(year=now.year - 1)
        elif date_str == "今年":
            return now
        elif date_str == "明年":
            return now.replace(year=now.year + 1)
        
        # 处理具体日期格式
        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d",      # 2023-01-01
            "%Y/%m/%d",      # 2023/01/01
            "%Y年%m月%d日",   # 2023年1月1日
            "%m/%d/%Y",      # 01/01/2023
            "%d/%m/%Y",      # 01/01/2023
            "%Y-%m-%d %H:%M:%S",  # 2023-01-01 12:00:00
            "%Y/%m/%d %H:%M:%S",  # 2023/01/01 12:00:00
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # 尝试解析"X天前"、"X天后"等格式
        match = re.match(r"(\d+)([天|周|月|年])前", date_str)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            if unit == "天":
                return now - timedelta(days=num)
            elif unit == "周":
                return now - timedelta(weeks=num)
            elif unit == "月":
                return now.replace(month=now.month - num) if now.month > num else now.replace(year=now.year - 1, month=12 + now.month - num)
            elif unit == "年":
                return now.replace(year=now.year - num)
        
        match = re.match(r"(\d+)([天|周|月|年])后", date_str)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            if unit == "天":
                return now + timedelta(days=num)
            elif unit == "周":
                return now + timedelta(weeks=num)
            elif unit == "月":
                return now.replace(month=now.month + num) if now.month + num <= 12 else now.replace(year=now.year + 1, month=num - 12)
            elif unit == "年":
                return now.replace(year=now.year + num)
        
        return None
    
    @staticmethod
    def parse_date_to_string(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[str]:
        """
        解析自然语言日期描述为指定格式的字符串
        
        Args:
            date_str: 自然语言日期描述
            format_str: 输出日期格式，默认为"%Y-%m-%d"
            
        Returns:
            格式化后的日期字符串或None
        """
        date_obj = DateConverter.parse_date(date_str)
        if date_obj:
            return date_obj.strftime(format_str)
        return None
    
    @staticmethod
    def get_date_range(start_date: str, end_date: str) -> list[datetime]:
        """
        获取日期范围内的所有日期
        
        Args:
            start_date: 开始日期（自然语言描述）
            end_date: 结束日期（自然语言描述）
            
        Returns:
            日期对象列表
        """
        start = DateConverter.parse_date(start_date)
        end = DateConverter.parse_date(end_date)
        
        if not start or not end:
            return []
        
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    @staticmethod
    def get_date_range_strings(start_date: str, end_date: str, format_str: str = "%Y-%m-%d") -> list[str]:
        """
        获取日期范围内的所有日期字符串
        
        Args:
            start_date: 开始日期（自然语言描述）
            end_date: 结束日期（自然语言描述）
            format_str: 输出日期格式，默认为"%Y-%m-%d"
            
        Returns:
            格式化后的日期字符串列表
        """
        dates = DateConverter.get_date_range(start_date, end_date)
        return [date.strftime(format_str) for date in dates]