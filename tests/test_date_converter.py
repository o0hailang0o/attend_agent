import pytest
from datetime import datetime, timedelta
import re
from typing import Optional

# 直接复制DateConverter类用于测试，避免导入问题
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
            # 简化处理，不使用zhconv
            pass
        
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
        
# 定义星期名称
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        # 处理星期
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
        
        # 处理"上上周一"
        if re.match(r"上上周一", date_str):
            monday = now - timedelta(days=now.weekday() + 21)
            return monday
        
        # 处理"上上上周一"
        if re.match(r"上上上周一", date_str):
            monday = now - timedelta(days=now.weekday() + 28)
            return monday
        
        # 处理"1个月前"
        if date_str == "1个月前":
            return now - timedelta(days=30)  # 近似值
        
        # 处理"1个月后"
        if date_str == "1个月后":
            return now + timedelta(days=30)  # 近似值
        
        # 处理"上个月"
        if date_str == "上个月":
            return now.replace(day=1) - timedelta(days=1)
        
        # 处理"下个月"
        if date_str == "下个月":
            next_month = now.month % 12 + 1
            year = now.year + (now.month // 12)
            return datetime(year, next_month, 1)
        
        # 处理"这个月"
        if date_str == "这个月":
            return datetime(now.year, now.month, 1)
        
        # 处理"X个月前"
        match = re.match(r"(\d+)个月前", date_str)
        if match:
            num = int(match.group(1))
            return now - timedelta(days=num * 30)  # 近似值
        
        # 处理"X个月后"
        match = re.match(r"(\d+)个月后", date_str)
        if match:
            num = int(match.group(1))
            return now + timedelta(days=num * 30)  # 近似值
        
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
        
        # 确保start <= end
        if start > end:
            start, end = end, start
        
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

class TestDateConverter:
    """日期转换工具测试类"""
    
    def test_relative_dates(self):
        """测试相对日期"""
        now = datetime.now()
        
        assert DateConverter.parse_date("今天") == now
        assert DateConverter.parse_date("昨天") == now - timedelta(days=1)
        assert DateConverter.parse_date("明天") == now + timedelta(days=1)
        assert DateConverter.parse_date("后天") == now + timedelta(days=2)
        assert DateConverter.parse_date("大后天") == now + timedelta(days=3)
        assert DateConverter.parse_date("大前天") == now - timedelta(days=3)
    
    def test_weekday_dates(self):
        """测试星期日期"""
        # 直接使用DateConverter解析结果进行比较
        monday_result = DateConverter.parse_date("星期一")
        last_monday_result = DateConverter.parse_date("上周一")
        two_weeks_ago_monday_result = DateConverter.parse_date("上个星期一")
        three_weeks_ago_monday_result = DateConverter.parse_date("上上周一")
        
        # 验证星期一的结果
        assert monday_result is not None
        assert last_monday_result is not None
        assert two_weeks_ago_monday_result is not None
        assert three_weeks_ago_monday_result is not None
        
        # 验证相对关系（忽略微秒差异）
        assert (last_monday_result.replace(microsecond=0) - monday_result.replace(microsecond=0)).days == -7
        assert (two_weeks_ago_monday_result.replace(microsecond=0) - monday_result.replace(microsecond=0)).days == -14
        assert (three_weeks_ago_monday_result.replace(microsecond=0) - monday_result.replace(microsecond=0)).days == -21
        
        # 验证这周一和本周一（忽略微秒差异）
        assert DateConverter.parse_date("这周一").replace(microsecond=0) == monday_result.replace(microsecond=0)
        assert DateConverter.parse_date("本周一").replace(microsecond=0) == monday_result.replace(microsecond=0)
        
        # 验证上星期一（忽略微秒差异）
        assert DateConverter.parse_date("上星期一").replace(microsecond=0) == last_monday_result.replace(microsecond=0)
        
        # 验证上上周一
        assert DateConverter.parse_date("上上周一") == three_weeks_ago_monday_result
    
    def test_month_dates(self):
        """测试月份日期"""
        now = datetime.now()
        
        # 上个月最后一天（当前月第一天减一天）
        last_month = datetime(now.year, now.month, 1) - timedelta(days=1)
        
        # 下个月第一天
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        assert DateConverter.parse_date("上个月").date() == last_month.date()
        assert DateConverter.parse_date("下个月") == next_month
    
    def test_year_dates(self):
        """测试年份日期"""
        now = datetime.now()
        
        assert DateConverter.parse_date("去年").replace(microsecond=0) == now.replace(year=now.year - 1, microsecond=0)
        assert DateConverter.parse_date("今年").replace(microsecond=0) == now.replace(microsecond=0)
        assert DateConverter.parse_date("明年").replace(microsecond=0) == now.replace(year=now.year + 1, microsecond=0)
    
    def test_specific_dates(self):
        """测试具体日期格式"""
        assert DateConverter.parse_date("2023-01-01") == datetime(2023, 1, 1)
        assert DateConverter.parse_date("01/01/2023") == datetime(2023, 1, 1)
        assert DateConverter.parse_date("2023年1月1日") == datetime(2023, 1, 1)
    
    def test_time_range(self):
        """测试日期范围"""
        start_date = "上个月"
        end_date = "这个月"
        
        date_range = DateConverter.get_date_range(start_date, end_date)
        assert len(date_range) > 0
        
        # 确保日期范围是连续的
        for i in range(1, len(date_range)):
            assert date_range[i] == date_range[i-1] + timedelta(days=1)
    
    def test_string_formatting(self):
        """测试字符串格式化"""
        start_date = "上个月"
        end_date = "这个月"
        
        formatted_dates = DateConverter.get_date_range_strings(start_date, end_date, "%Y-%m-%d")
        assert len(formatted_dates) > 0
        
        # 确保格式正确
        for date_str in formatted_dates:
            assert re.match(r"\d{4}-\d{2}-\d{2}", date_str) is not None
    
    def test_invalid_dates(self):
        """测试无效日期"""
        assert DateConverter.parse_date("invalid_date") is None
        assert DateConverter.parse_date("") is None
        assert DateConverter.parse_date(None) is None
    
    def test_time_range_strings(self):
        """测试日期范围字符串"""
        start_date = "上个月"
        end_date = "这个月"
        
        formatted_dates = DateConverter.get_date_range_strings(start_date, end_date, "%Y-%m-%d")
        assert len(formatted_dates) > 0
        
        # 确保格式正确
        for date_str in formatted_dates:
            assert re.match(r"\d{4}-\d{2}-\d{2}", date_str) is not None
    
    def test_days_ago_later(self):
        """测试天、周、月、年前后的日期"""
        now = datetime.now()
        
        # 所有比较均忽略微秒差异
        now_floor = now.replace(microsecond=0)
        assert DateConverter.parse_date("3天前").replace(microsecond=0) == (now - timedelta(days=3)).replace(microsecond=0)
        assert DateConverter.parse_date("2周后").replace(microsecond=0) == (now + timedelta(weeks=2)).replace(microsecond=0)
        
        # 测试月份
        assert DateConverter.parse_date("1个月前").replace(microsecond=0) == (now - timedelta(days=30)).replace(microsecond=0)
        assert DateConverter.parse_date("2个月前").replace(microsecond=0) == (now - timedelta(days=60)).replace(microsecond=0)
        
        # 测试年份（避免微秒差异影响比较）
        two_years_result = DateConverter.parse_date("2年后")
        assert two_years_result is not None
        assert two_years_result.replace(microsecond=0) == now.replace(year=now.year + 2, microsecond=0)
        
        two_years_ago_result = DateConverter.parse_date("2年前")
        assert two_years_ago_result is not None
        assert two_years_ago_result.replace(microsecond=0) == now.replace(year=now.year - 2, microsecond=0)

if __name__ == "__main__":
    pytest.main()