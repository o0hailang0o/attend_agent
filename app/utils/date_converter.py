import logging
from datetime import datetime, timedelta
import re
from typing import Union, Optional
import zhconv

logger = logging.getLogger(__name__)

class DateConverter:
    """日期转换工具，支持自然语言日期描述转换为实际日期"""
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        解析自然语言日期描述为datetime对象
        
         支持的格式：
        - 今天、昨天、明天、后天、大后天、大前天
        - 本周、上周、下周、下下周、大下周、本周末、上周末、下周末
        - 周一~周日、星期一~星期日（本周内往后找最近的一天）
        - 这/本周一~日、上/上周一~日、下/下周 一~日
        - 上个、上上个、下个、下下、大上、大下 + 周一~日
        - 传统节日：元旦、春节、除夕、元宵节、清明节、劳动节、五一劳动节、
          五四、端午节、七夕节、中元节、中秋节、国庆节、十一、重阳节、圣诞节
        - 上个月、这个月/本月、下个月
        - 去年、今年、明年
        - X月X日、X月X号
        - X天/周/月/年前、X天/周/月/年后
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

        # 处理传统节日（部分按农历，此处按当前年份的估算日期）
        FESTIVALS = {
            "元旦":                     (1, 1),
            "春节":                     (2, 17),   # 2026年农历正月初一
            "除夕":                     (2, 16),   # 2026年农历腊月三十
            "元宵节":                   (3, 3),    # 2026年农历正月十五
            "清明节":                   (4, 5),
            "劳动节":                   (5, 1),
            "五一":                     (5, 1),
            "五一劳动节":               (5, 1),
            "五四":                     (5, 4),
            "端午节":                   (6, 19),   # 2026年农历五月初五
            "七夕节":                   (8, 27),   # 2026年农历七月初七
            "七夕":                     (8, 27),
            "中元节":                   (9, 5),    # 2026年农历七月十五
            "中秋节":                   (10, 4),   # 2026年农历八月十五
            "国庆节":                   (10, 1),
            "十一":                     (10, 1),
            "重阳节":                   (10, 28),  # 2026年农历九月初九
            "圣诞节":                   (12, 25),
        }
        if date_str in FESTIVALS:
            month, day = FESTIVALS[date_str]
            try:
                return now.replace(month=month, day=day)
            except ValueError:
                pass

        # 处理"本周/上周/下周/本周末/上周末/下周末"等
        WEEK_OFFSETS = {
            "本周": 0, "这周": 0, "上周": -1, "下周": 1, "下下周": 2, "大下周": 2,
            "本周末": 0, "这周末": 0, "上周末": -1, "下周末": 1,
        }
        if date_str in WEEK_OFFSETS:
            offset = WEEK_OFFSETS[date_str]
            if "末" in date_str:
                # 周末 = 周日
                return now + timedelta(days=6 - now.weekday()) + timedelta(weeks=offset)
            return now - timedelta(days=now.weekday()) + timedelta(weeks=offset)

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
            return now + timedelta(days=target_weekday - now.weekday())
        
        # 处理"这/本周X"、"上/上周X"、"下/下周X"、"上个X"
        for prefix, weeks_offset in [("大上", -2), ("上上个", -2), ("上上", -2), ("上个", -1), ("上", -1),
                                      ("这", 0), ("本", 0), ("下个", 1), ("下", 1), ("下下", 2), ("大下", 2)]:
            for wd_name, wd_idx in zip(weekday_names + weekdays, list(range(7)) * 2):
                if date_str == f"{prefix}{wd_name}":
                    target = now - timedelta(days=now.weekday() - wd_idx) + timedelta(weeks=weeks_offset)
                    return target
        
        # 处理"上个月X号/日"、"下个月X号/日"、"这个月X号/日"、"本月X号/日"
        match = re.match(r"(?:上个月|下个月|这个月|本月)(\d{1,2})(?:日|号)", date_str)
        if match:
            day = int(match.group(1))
            if "上个月" in date_str:
                base = now.replace(day=1) - timedelta(days=1)
                month, year = base.month, base.year
            elif "下个月" in date_str:
                month = now.month % 12 + 1
                year = now.year + (now.month // 12)
            else:
                month, year = now.month, now.year
            return datetime(year, month, day)

        if date_str == "上个月":
            return (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        elif date_str == "这个月" or date_str == "本月":
            return now.replace(day=1)
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
            "%y年%m月%d日",   # 25年5月20日 → 2025
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
        
        # 处理"X月X日"、"X月X号"（默认当年）
        match = re.match(r"(\d{1,2})月(\d{1,2})(?:日|号)$", date_str)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            return now.replace(month=month, day=day, hour=0, minute=0, second=0, microsecond=0)

        # 处理"X日"、"X号"（默认当月当年）
        match = re.match(r"(\d{1,2})(?:日|号)$", date_str)
        if match:
            day = int(match.group(1))
            return now.replace(day=day, hour=0, minute=0, second=0, microsecond=0)

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
    def _llm_parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[str]:
        """调用大模型解析日期，作为规则解析的兜底"""
        try:
            from llama_index.core import Settings as LlamaSettings
            from llama_index.core.llms import ChatMessage, MessageRole
            llm = LlamaSettings.llm
            if not llm:
                logger.warning("LLM 未初始化，跳过 LLM 日期解析")
                return None
            logger.info("LLM 日期解析请求: '%s' -> 模型=%s", date_str, llm.model if hasattr(llm, 'model') else 'unknown')
            prompt = (
                f"你是一个日期解析工具。请将以下中文日期描述转换为{format_str}格式。"
                f"只返回日期本身，不要任何解释、不要标点、不要多余字符。\n"
                f"日期描述：{date_str}"
            )
            resp = llm.chat([ChatMessage(role=MessageRole.USER, content=prompt)])
            text = resp.message.content.strip().strip('"').strip("'")
            parsed = datetime.strptime(text, format_str)
            result = parsed.strftime(format_str)
            logger.info("LLM 日期解析成功: '%s' -> %s", date_str, result)
            return result
        except Exception as e:
            logger.warning("LLM 日期解析失败 '%s': %s", date_str, e)
            return None

    @staticmethod
    def parse_date_to_string(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[str]:
        """
        解析自然语言日期描述为指定格式的字符串。
        1. 输入已是 YYYY-MM-DD 格式 → 直接返回
        2. 规则解析
        3. 规则失败 → 调用大模型兜底

        Args:
            date_str: 自然语言日期描述
            format_str: 输出日期格式，默认为"%Y-%m-%d"

        Returns:
            格式化后的日期字符串或None
        """
        if not date_str:
            return None
        s = date_str.strip()
        # 已经是目标格式 → 直接返回
        try:
            datetime.strptime(s, format_str)
            logger.debug("日期已是标准格式: '%s'", s)
            return s
        except ValueError:
            pass
        logger.info("开始日期转换: '%s'", s)
        date_obj = DateConverter.parse_date(s)
        if date_obj:
            logger.debug("规则解析成功: '%s' -> %s", s, date_obj.strftime(format_str))
            return date_obj.strftime(format_str)
        logger.info("规则无法解析 '%s'，调用 LLM 兜底", s)
        return DateConverter._llm_parse_date(s, format_str)
    
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