import os
from datetime import datetime, date
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# 学期配置
SEMESTER_START_STR = os.getenv("SEMESTER_START_DATE", "2026-03-02")
SEMESTER_START = datetime.strptime(SEMESTER_START_STR, "%Y-%m-%d").date()

def get_current_week(reference_date: Optional[date] = None) -> int:
    """
    计算当前日期是学期第几周。
    规则：周一为一周的开始，学期开始日期所在周为第1周。
    """
    if reference_date is None:
        reference_date = date.today()
    days_diff = (reference_date - SEMESTER_START).days
    if days_diff < 0:
        return 0
    week_num = days_diff // 7 + 1
    return week_num