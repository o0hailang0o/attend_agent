import logging
import re
import time as _time
from datetime import time, timedelta, datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TimeConverter:

    _PERIOD_MAP = {
        "凌晨": 0, "早晨": 0, "早上": 0,
        "上午": 0,
        "中午": 0, "午间": 0,
        "下午": 12,
        "晚上": 12, "晚间": 12, "夜里": 12,
        "午夜": 0,
    }

    # 模糊时段 → 默认起止时间（兜底用，优先查数据库 rule 表）
    _PERIOD_DEFAULTS = {
        "上午": ("09:00", "12:00"),
        "中午": ("12:00", "14:00"),
        "下午": ("14:00", "18:00"),
        "晚上": ("18:00", "21:00"),
        "全天": ("09:00", "18:00"),
    }

    # rule 缓存：user_uuid → (expiry_timestamp, periods_dict)
    _rule_cache: dict[str, tuple[float, dict]] = {}
    _RULE_CACHE_TTL = 300  # 5 分钟

    @staticmethod
    def _fmt_time(val) -> str:
        """将数据库返回的时间值统一转为 HH:MM 字符串"""
        if val is None:
            return ""
        if isinstance(val, time):
            return val.strftime("%H:%M")
        s = str(val)
        return s[:5] if len(s) >= 5 else s

    @staticmethod
    def _get_user_rule_periods(user_uuid: str) -> dict:
        """查询用户所属考勤规则，返回动态时段默认值。查不到时回落 _PERIOD_DEFAULTS。"""
        if not user_uuid:
            return TimeConverter._PERIOD_DEFAULTS

        cached = TimeConverter._rule_cache.get(user_uuid)
        if cached and cached[0] > _time.time():
            return cached[1]

        try:
            from app.core.database import SessionLocal
            from sqlalchemy import text
            session = SessionLocal()
            try:
                user_row = session.execute(
                    text("SELECT rule_uuid FROM sys_user WHERE uuid = :uid AND is_delete = 1"),
                    {"uid": user_uuid}
                ).fetchone()
                if not user_row or not user_row[0]:
                    return TimeConverter._PERIOD_DEFAULTS

                rule_uuid = str(user_row[0])
                rule_row = session.execute(
                    text("SELECT start_time, end_time, middle_start, middle_end, middle_rest "
                         "FROM rule WHERE uuid = :ruid AND is_delete = 1"),
                    {"ruid": rule_uuid}
                ).fetchone()
                if not rule_row:
                    return TimeConverter._PERIOD_DEFAULTS

                start = TimeConverter._fmt_time(rule_row[0]) or "09:00"
                end = TimeConverter._fmt_time(rule_row[1]) or "18:00"
                m_start = TimeConverter._fmt_time(rule_row[2]) or "12:00"
                m_end = TimeConverter._fmt_time(rule_row[3]) or "14:00"
                has_middle = int(rule_row[4]) if rule_row[4] else 0

                periods = {}
                if has_middle:
                    periods["上午"] = (start, m_start)
                    periods["中午"] = (m_start, m_end)
                    periods["下午"] = (m_end, end)
                else:
                    periods["上午"] = (start, "12:00")
                    periods["下午"] = ("12:00", end)
                periods["晚上"] = (end, "21:00")
                periods["全天"] = (start, end)

                TimeConverter._rule_cache[user_uuid] = (_time.time() + TimeConverter._RULE_CACHE_TTL, periods)
                return periods
            finally:
                session.close()
        except Exception:
            return TimeConverter._PERIOD_DEFAULTS

    @staticmethod
    def resolve_period_range(date_str: str, time_text: str, user_uuid: str = "", fmt: str = "%Y-%m-%dT%H:%M:%S") -> tuple[Optional[str], Optional[str]]:
        """识别模糊时段描述（如"下午请假"、"上午"）→ 补全默认起止时间（优先查数据库 rule）"""
        from app.utils.date_converter import DateConverter
        periods = TimeConverter._get_user_rule_periods(user_uuid)
        for period, (def_start, def_end) in periods.items():
            if period in time_text:
                date_obj = DateConverter.parse_date(date_str) if date_str else None
                if date_obj is None:
                    return None, None
                d = date_obj.strftime("%Y-%m-%d")
                return f"{d}T{def_start}:00", f"{d}T{def_end}:00"
        return None, None

    @staticmethod
    def parse_time(time_str: str) -> Optional[time]:
        """解析时分秒字符串 → datetime.time"""
        if not time_str:
            return None
        s = time_str.strip()

        m = re.match(
            r'^(凌晨|早晨|早上|上午|中午|午间|下午|晚上|晚间|夜里|午夜)?'
            r'(\d{1,2})点'
            r'(?:(\d{1,2})(?:分)?)?$', s
        )
        if m:
            period_offset = TimeConverter._PERIOD_MAP.get(m[1] or "上午", 0)
            h = int(m[2]) + period_offset
            mi = int(m[3]) if m[3] else 0
            if h > 23 or mi > 59:
                return None
            return time(h, mi)

        match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', s)
        if match:
            h, m, sec = int(match[1]), int(match[2]), int(match[3]) if match[3] else 0
            if h > 23 or m > 59 or sec > 59:
                return None
            return time(h, m, sec)

        return None

    @staticmethod
    def format_time(t: Optional[time], with_seconds: bool = False) -> str:
        if t is None:
            return ""
        if with_seconds:
            return t.strftime("%H:%M:%S")
        return t.strftime("%H:%M")

    @staticmethod
    def parse_duration(text: str) -> Optional[timedelta]:
        """解析时长文本 → timedelta"""
        if not text:
            return None
        s = text.strip()

        m = re.match(r'^(\d+(?:\.\d+)?)小时(?:\s*(\d+(?:\.\d+)?)(?:分钟|分))?$', s)
        if m:
            return timedelta(hours=float(m[1]), minutes=float(m[2]) if m[2] else 0)

        m = re.match(r'^(\d+(?:\.\d+)?)(?:分钟|分)$', s)
        if m:
            return timedelta(minutes=float(m[1]))

        m = re.match(r'^(\d+(?:\.\d+)?)h(?:\s*(\d+(?:\.\d+)?)m)?$', s, re.IGNORECASE)
        if m:
            return timedelta(hours=float(m[1]), minutes=float(m[2]) if m[2] else 0)

        m = re.match(r'^(\d+(?:\.\d+)?)m$', s, re.IGNORECASE)
        if m:
            return timedelta(minutes=float(m[1]))

        m = re.match(r'^(\d+):(\d{2})(?::(\d{2}))?$', s)
        if m:
            return timedelta(hours=int(m[1]), minutes=int(m[2]), seconds=int(m[3]) if m[3] else 0)

        m = re.match(r'^(\d+(?:\.\d+)?)$', s)
        if m:
            return timedelta(hours=float(m[1]))

        return None

    @staticmethod
    def format_duration(d: Optional[timedelta], fmt: str = "auto") -> str:
        if d is None:
            return ""
        total_seconds = int(d.total_seconds())
        negative = total_seconds < 0
        if negative:
            total_seconds = -total_seconds
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        sign = "-" if negative else ""

        if fmt == "H:M":
            return f"{sign}{hours}:{minutes:02d}"
        if fmt == "H:M:S":
            return f"{sign}{hours}:{minutes:02d}:{seconds:02d}"
        if fmt in ("auto", "chinese"):
            parts = []
            if hours:
                parts.append(f"{hours}小时")
            if minutes:
                parts.append(f"{minutes}分钟")
            if not hours and not minutes and seconds:
                parts.append(f"{seconds}秒")
            if not parts:
                return "0分钟"
            return sign + "".join(parts)
        return str(d)

    @staticmethod
    def parse_datetime(text: str) -> Optional[datetime]:
        """解析常见日期时间字符串 → datetime"""
        if not text:
            return None
        s = text.strip()

        patterns = [
            (r'^(\d{4})-(\d{1,2})-(\d{1,2})[T ](\d{1,2}):(\d{2})(?::(\d{2}))?$',
             lambda m: datetime(int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6] or 0))),
            (r'^(\d{4})/(\d{1,2})/(\d{1,2})[T ](\d{1,2}):(\d{2})(?::(\d{2}))?$',
             lambda m: datetime(int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6] or 0))),
            (r'^(\d{4})[年](\d{1,2})[月](\d{1,2})[日] (\d{1,2}):(\d{2})(?::(\d{2}))?$',
             lambda m: datetime(int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6] or 0))),
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})[T ](\d{1,2}):(\d{2})(?::(\d{2}))?$',
             lambda m: datetime(int(m[3]), int(m[1]), int(m[2]), int(m[4]), int(m[5]), int(m[6] or 0))),
            (r'^(\d{4})-(\d{1,2})-(\d{1,2})$',
             lambda m: datetime(int(m[1]), int(m[2]), int(m[3]))),
            (r'^(\d{4})/(\d{1,2})/(\d{1,2})$',
             lambda m: datetime(int(m[1]), int(m[2]), int(m[3]))),
        ]

        for pattern, builder in patterns:
            m = re.match(pattern, s)
            if m:
                try:
                    return builder(m)
                except ValueError:
                    return None
        return None

    @staticmethod
    def format_datetime(dt: Optional[datetime], with_seconds: bool = True) -> str:
        if dt is None:
            return ""
        if with_seconds:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def combine_date_time(date_str: str, time_str: str) -> Optional[datetime]:
        """自然语言日期 + 自然语言时间 → datetime"""
        from app.utils.date_converter import DateConverter
        d = DateConverter.parse_date(date_str)
        if d is None:
            return None
        t = TimeConverter.parse_time(time_str)
        if t is None:
            return None
        return datetime.combine(d.date(), t)

    @staticmethod
    def parse_datetime_range(
        date_str: str,
        start_str: str,
        end_str: Optional[str] = None,
        fmt: str = "%Y-%m-%d %H:%M:%S",
    ) -> tuple[Optional[str], Optional[str]]:
        start = TimeConverter.combine_date_time(date_str, start_str)
        if start is None:
            return None, None
        if end_str is None:
            return start.strftime(fmt), None
        end = TimeConverter.combine_date_time(date_str, end_str)
        if end is not None and end < start:
            has_period = re.match(r'^(凌晨|早晨|早上|上午|中午|午间|下午|晚上|晚间|夜里|午夜)', end_str.strip())
            if not has_period:
                raw_match = re.search(r'(\d{1,2})点', end_str.strip())
                if raw_match:
                    raw_hour = int(raw_match.group(1))
                    for period, offset in TimeConverter._PERIOD_MAP.items():
                        if start_str.strip().startswith(period):
                            adjusted_hour = raw_hour + offset
                            if adjusted_hour <= 23:
                                end = datetime.combine(start.date(), time(adjusted_hour, end.minute, end.second))
                            break
        return start.strftime(fmt), end.strftime(fmt) if end else None

    @staticmethod
    def _llm_parse_range(text: str) -> tuple[Optional[str], Optional[str]]:
        """调用大模型解析时间范围，作为规则解析的兜底"""
        try:
            from llama_index.core import Settings as LlamaSettings
            from llama_index.core.llms import ChatMessage, MessageRole
            llm = LlamaSettings.llm
            if not llm:
                logger.warning("_llm_parse_range: LlamaSettings.llm 为 None，尝试初始化")
                try:
                    from app.core.llama_index import get_llm
                    get_llm()
                    llm = LlamaSettings.llm
                except Exception as e:
                    logger.error("_llm_parse_range: 初始化 LLM 失败: %s", e)
            if not llm:
                logger.warning("_llm_parse_range: LLM 仍不可用，返回 None")
                return None, None
            logger.info("_llm_parse_range: 调用 LLM 解析时间: '%s'", text)
            prompt = (
                "你是一个时间解析工具。请将以下中文时间描述解析为起始和结束时间。\n"
                "只返回两行，不要任何解释：\n"
                "第一行: start=YYYY-MM-ddTHH:mm:ss\n"
                "第二行: end=YYYY-MM-ddTHH:mm:ss（如果只有单个时间，end=空）\n\n"
                f"时间描述：{text}"
            )
            resp = llm.chat([ChatMessage(role=MessageRole.USER, content=prompt)])
            raw = (resp.message.content or "").strip()
            start = end = None
            for line in raw.split("\n"):
                line = line.strip()
                if line.startswith("start="):
                    start = line[6:].strip()
                elif line.startswith("end="):
                    val = line[4:].strip()
                    end = val if val and val != "空" else None
            # validate format
            import datetime as _dt
            if start:
                try:
                    start = _dt.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    start = None
            if end:
                try:
                    end = _dt.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    end = None
            return start, end
        except Exception:
            return None, None

    @staticmethod
    def parse_natural_range(text: str, user_uuid: str = "", fmt: str = "%Y-%m-%dT%H:%M:%S") -> tuple[Optional[str], Optional[str]]:
        """解析完整自然语言时间范围 → ("YYYY-MM-ddTHH:mm:ss", "YYYY-MM-ddTHH:mm:ss")"""
        if not text:
            return None, None
        s = text.strip()

        from app.utils.date_converter import DateConverter

        parts = re.split(r'[，,;\s]+', s, maxsplit=1)
        date_part = None
        time_part = None

        if len(parts) == 2:
            candidate_date, rest = parts[0].strip(), parts[1].strip()
            if DateConverter.parse_date(candidate_date) is not None:
                date_part = candidate_date
                time_part = rest

        if date_part is None:
            # 尝试从开头截取日期前缀，如 "5月27日上午3点到4点" → "5月27日"
            for split_pos in range(len(s) - 1, 0, -1):
                candidate = s[:split_pos]
                if DateConverter.parse_date(candidate) is not None:
                    date_part = candidate
                    time_part = s[split_pos:]
                    break
            # 截取失败时尝试整个字符串作为纯日期
            if date_part is None:
                dt = TimeConverter.combine_date_time(s, "0:00")
                if dt:
                    return dt.strftime(fmt), None

        if date_part and time_part:
            time_parts = re.split(r'[到至\-—~～]', time_part, maxsplit=1)
            start_str = time_parts[0].strip()
            end_str = time_parts[1].strip() if len(time_parts) > 1 else None
            if end_str is None and ' ' in time_part.strip():
                space_parts = time_part.strip().split(None, 1)
                if len(space_parts) == 2:
                    start_str, end_str = space_parts[0].strip(), space_parts[1].strip()
            result = TimeConverter.parse_datetime_range(date_part, start_str, end_str, fmt=fmt)
            if result != (None, None):
                return result

        # 模糊时段兜底（如"明天下午请假" → 根据用户所属 rule 补全时间）
        if date_part and time_part:
            result = TimeConverter.resolve_period_range(date_part, time_part, user_uuid=user_uuid, fmt=fmt)
            if result != (None, None):
                return result

        # 规则解析失败 → LLM 兜底
        return TimeConverter._llm_parse_range(s)
    
    
if __name__ == '__main__':
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    from app.core.llama_index import get_llm
    try:
        get_llm()
        print("LLM 初始化成功")
    except Exception as e:
        print(f"LLM 初始化失败: {e}")
    start_str, end_str = TimeConverter.parse_natural_range(text = "上班一天时间")
    print(start_str, end_str)
        
        
