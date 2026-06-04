import os
from datetime import datetime, date
from typing import Optional
from langchain_core.tools import tool

# 导入工具函数需要的模块
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campus_crawler.crawler.cuit_crawler import CUITCrawler
from campus_crawler.crawler.parse_course_table import parse_course_table
from campus_crawler.crawler.parse_grade_table import parse_grade_table
from campus_crawler.crawler.parse_exam_table import parse_exam_table
from utils.week_utils import get_current_week, SEMESTER_START

# ==================== 全局爬虫实例管理 ====================
_crawler_sessions = {}

def get_crawler(username: str = None, password: str = None):
    """获取爬虫实例，支持多用户会话"""
    if username and password:
        if username not in _crawler_sessions:
            crawler = CUITCrawler()
            crawler.login(username, password)
            _crawler_sessions[username] = crawler
            print(f"✅ 创建新会话: {username}")
        return _crawler_sessions[username]
    else:
        return CUITCrawler()

# ==================== 实时爬虫工具（需要登录） ====================
@tool
def fetch_live_courses(username: str, password: str, weekday: Optional[str] = None) -> str:
    """
    【优先使用】实时从教务系统获取课表数据。
    """
    try:
        crawler = get_crawler(username, password)
        html = crawler.get_course_table()
        result = parse_course_table(html)
        
        # 如果没有指定weekday，返回完整的课程列表
        if weekday is None:
            courses = result.get('courses', [])
            if not courses:
                return "未找到课程数据"
            
            lines = [f"📚 本学期共 {len(courses)} 门课程：", ""]
            for i, c in enumerate(courses, 1):
                lines.append(f"{i}. {c['name']}")
                lines.append(f"   教师：{c['teacher']} | 班级：{c['class_name']} | 学分：{c['credit']}")
                lines.append("")
            return "\n".join(lines)
        
        # 有weekday，返回指定天的课表
        weekday_map = {'周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6}
        if weekday not in weekday_map:
            return f"无法识别星期：{weekday}，请使用'周一'至'周日'"
        
        # 加载时间表
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        time_table_path = os.path.join(DATA_DIR, 'time.txt')
        period_times = {}
        if os.path.exists(time_table_path):
            import re
            with open(time_table_path, 'r', encoding='utf-8') as f:
                for line in f:
                    m = re.search(r'第(\d+)节(\d{2}:\d{2}-\d{2}:\d{2})', line)
                    if m:
                        period_times[int(m.group(1))] = m.group(2)
        
        current_week = get_current_week()
        filtered = [s for s in result['schedule'] if s['day'] == weekday]
        
        if not filtered:
            return f"{weekday}暂无课程安排"
        
        # 按节次排序
        filtered.sort(key=lambda x: x['section'])
        
        lines = [f"📅 {weekday}的课程（第{current_week}周）："]
        for s in filtered:
            weeks_text = s.get('weeks_text', '')
            has_class = False
            if weeks_text and '-' in weeks_text:
                parts = weeks_text.split('-')
                if len(parts) == 2:
                    start, end = int(parts[0]), int(parts[1])
                    has_class = start <= current_week <= end
            
            status = "✅ 本周有课" if has_class else "⏸️ 本周无课"
            time_str = f"（{period_times.get(s['section'], '')}）" if period_times.get(s['section']) else ""
            lines.append(f"  {s['section']}节{time_str}：{s['course_name']}，教室：{s['room']}，周次：{weeks_text} {status}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ 获取课表失败：{str(e)}"

@tool
def fetch_live_grades(username: str, password: str, semester_id: Optional[str] = None) -> str:
    """
    【优先使用】实时从教务系统获取成绩数据。
    """
    try:
        crawler = get_crawler(username, password)
        html = crawler.get_grade_table(semester_id)
        result = parse_grade_table(html)
        
        stats = result.get('stats', {})
        courses = result.get('courses', [])
        
        if not courses:
            return "暂无成绩数据"
        
        lines = [
            "📊 成绩统计",
            "=" * 30,
            f"📚 总课程数：{stats.get('total_courses', 0)}",
            f"📖 总学分：{stats.get('total_credits', 0)}",
            f"⭐ 平均绩点：{stats.get('avg_gpa', 0)}",
            f"📈 平均分：{stats.get('avg_score', 0)}",
            "",
            "📋 成绩明细："
        ]
        
        for c in courses:
            lines.append(f"  • {c['course_name']}：{c['total_score']}分，绩点{c['gpa']}，学分{c['credit']}")
        
        category_stats = stats.get('category_stats', {})
        if category_stats:
            lines.append("")
            lines.append("📂 按类别统计：")
            for cat, data in category_stats.items():
                lines.append(f"  • {cat}：{data['courses']}门，学分{data['total_credits']}，平均绩点{data['avg_gpa']}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ 获取成绩失败：{str(e)}"

@tool
def fetch_live_current_course(username: str, password: str, campus: Optional[str] = None) -> str:
    """
    【优先使用】实时获取当前正在上的课程或下一节课。
    """
    try:
        crawler = get_crawler(username, password)
        html = crawler.get_course_table()
        result = parse_course_table(html)
        
        now = datetime.now()
        weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()]
        current_week = get_current_week()
        
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        
        def parse_time_table(file_path):
            import re
            campus_times = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            header = lines[0].strip()
            parts = header.split()
            campus_names = [p for p in parts[1:] if p] or ['航空港校区', '龙泉校区']
            for name in campus_names:
                campus_times[name] = [None] * 12
            pattern = re.compile(r'第(\d+)节(\d{2}:\d{2}-\d{2}:\d{2})\s+(\d{2}:\d{2}-\d{2}:\d{2})')
            for line in lines:
                m = pattern.search(line)
                if m:
                    period_idx = int(m.group(1)) - 1
                    if 0 <= period_idx < 12:
                        time1 = m.group(2)
                        time2 = m.group(3)
                        for i, name in enumerate(campus_names):
                            time_str = time1 if i == 0 else time2
                            start_str, end_str = time_str.split('-')
                            start_time = datetime.strptime(start_str, '%H:%M').time()
                            end_time = datetime.strptime(end_str, '%H:%M').time()
                            campus_times[name][period_idx] = (start_time, end_time)
            return campus_times
        
        time_table_path = os.path.join(DATA_DIR, 'time.txt')
        if not os.path.exists(time_table_path):
            return "时间表文件不存在，无法判断当前课程"
        
        time_table = parse_time_table(time_table_path)
        use_campus = campus if campus and campus in time_table else '航空港校区'
        times = time_table.get(use_campus, time_table.get('航空港校区', []))
        
        current_time = now.time()
        current_period = None
        for i, (start, end) in enumerate(times):
            if start and start <= current_time <= end:
                current_period = i + 1
                break
        
        period_names = [f'第{i+1}节' for i in range(12)]
        
        for s in result['schedule']:
            if s['day'] == weekday_cn and s['section'] == current_period:
                weeks_text = s.get('weeks_text', '')
                if weeks_text and '-' in weeks_text:
                    parts = weeks_text.split('-')
                    if len(parts) == 2:
                        start_week, end_week = int(parts[0]), int(parts[1])
                        if start_week <= current_week <= end_week:
                            return f"🕐 当前正在上：{s['course_name']}（{s.get('teacher', '未知')}）@ {s['room']}\n📅 第{current_week}周 {weekday_cn} 第{current_period}节"
        
        next_period = None
        for i, (start, end) in enumerate(times):
            if start and start > current_time:
                next_period = i + 1
                break
        
        if next_period:
            for s in result['schedule']:
                if s['day'] == weekday_cn and s['section'] == next_period:
                    weeks_text = s.get('weeks_text', '')
                    if weeks_text and '-' in weeks_text:
                        parts = weeks_text.split('-')
                        if len(parts) == 2:
                            start_week, end_week = int(parts[0]), int(parts[1])
                            if start_week <= current_week <= end_week:
                                return f"⏭️ 下一节课是：{s['course_name']}（{s.get('teacher', '未知')}）@ {s['room']}\n📅 第{current_week}周 {weekday_cn} 第{next_period}节"
        
        if current_period:
            return f"📭 当前{weekday_cn}第{current_period}节无课程安排"
        else:
            return f"📭 今天没有更多课程了"
        
    except Exception as e:
        return f"❌ 获取实时课程失败：{str(e)}"

@tool
def fetch_live_exams(username: str, password: str) -> str:
    """
    【优先使用】实时从教务系统获取考试安排。
    """
    try:
        crawler = get_crawler(username, password)
        html = crawler.get_exam_table()
        result = parse_exam_table(html)
        
        exams = result.get('exams', [])
        stats = result.get('stats', {})
        
        if not exams:
            return "暂无考试安排数据"
        
        lines = [
            "📋 考试安排",
            "=" * 30,
            f"📚 总考试数：{stats.get('total_exams', 0)}",
            f"✅ 已安排：{stats.get('scheduled_exams', 0)}",
            f"⏳ 未安排：{stats.get('unscheduled_exams', 0)}",
            "",
            "📅 考试明细："
        ]
        
        for exam in exams:
            # 处理日期和时间的显示
            exam_date = exam['exam_date'] if exam['exam_date'] and exam['exam_date'] != '待定' else '待定'
            exam_time = exam['exam_time'] if exam['exam_time'] and exam['exam_time'] != '待定' else '待定'
            exam_location = exam['exam_location'] if exam['exam_location'] and exam['exam_location'] != '待定' else '待定'
            
            # 判断是否为已安排的考试
            is_scheduled = exam_date != '待定' and exam_time != '待定'
            status_icon = "✅" if is_scheduled else "⏳"
            
            lines.append(f"  {status_icon} {exam['course_name']}")
            lines.append(f"     类型：{exam['exam_type']} | 日期：{exam_date} | 时间：{exam_time} | 地点：{exam_location}")
            lines.append("")  # 添加空行分隔
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ 获取考试安排失败：{str(e)}"

# ==================== 原有工具（基于本地文件，作为备用） ====================
# 获取data目录路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

def load_course_data():
    """加载课表数据（从本地文件）"""
    course_html_path = os.path.join(DATA_DIR, 'course_table.html')
    if os.path.exists(course_html_path):
        with open(course_html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        return parse_course_table(html)
    return {'courses': [], 'schedule': []}

def load_grade_data():
    """加载成绩数据（从本地文件）"""
    grade_html_path = os.path.join(DATA_DIR, 'grade_table.html')
    if os.path.exists(grade_html_path):
        with open(grade_html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        return parse_grade_table(html)
    return {'courses': [], 'stats': {}}

# 加载数据（作为备用）
course_result = load_course_data()
grade_result = load_grade_data()

course_list = course_result['courses']
schedule_raw = course_result['schedule']

# 构建课表矩阵
weekday_map = {'周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6}
period_names = [f'第{i+1}节' for i in range(12)]
schedule_matrix = [[None for _ in range(12)] for _ in range(7)]

for item in schedule_raw:
    day = weekday_map[item['day']]
    period = item['section'] - 1
    if 0 <= period < 12:
        schedule_matrix[day][period] = {
            'course_name': item['course_name'],
            'course_code': item['course_code_full'].split('(')[0] if '(' in item['course_code_full'] else item['course_code_full'],
            'teacher': '',
            'classroom': item['room'],
            'weeks_binary': item.get('weeks_binary', ''),
            'weeks_text': item.get('weeks_text', '')
        }

teacher_map = {c['name']: c['teacher'] for c in course_list}
for day in range(7):
    for period in range(12):
        if schedule_matrix[day][period]:
            course_name = schedule_matrix[day][period]['course_name']
            schedule_matrix[day][period]['teacher'] = teacher_map.get(course_name, '未知教师')

grade_stats = grade_result.get('stats', {})
grade_courses = grade_result.get('courses', [])

# 加载上课时间表
CAMPUS = os.getenv("CAMPUS", "航空港校区")

def parse_time_table(file_path: str):
    """解析时间表"""
    import re
    campus_times = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    header = lines[0].strip()
    parts = header.split()
    campus_names = [p for p in parts[1:] if p]
    if not campus_names:
        campus_names = ['航空港校区', '龙泉校区']
    
    for name in campus_names:
        campus_times[name] = [None] * 12
    
    pattern = re.compile(r'第(\d+)节(\d{2}:\d{2}-\d{2}:\d{2})\s+(\d{2}:\d{2}-\d{2}:\d{2})')
    
    for line in lines:
        m = pattern.search(line)
        if m:
            period_idx = int(m.group(1)) - 1
            if 0 <= period_idx < 12:
                time1 = m.group(2)
                time2 = m.group(3)
                for i, name in enumerate(campus_names):
                    time_str = time1 if i == 0 else time2
                    start_str, end_str = time_str.split('-')
                    start_time = datetime.strptime(start_str, '%H:%M').time()
                    end_time = datetime.strptime(end_str, '%H:%M').time()
                    campus_times[name][period_idx] = (start_time, end_time)
    return campus_times

time_table_path = os.path.join(DATA_DIR, 'time.txt')
if os.path.exists(time_table_path):
    time_table = parse_time_table(time_table_path)
else:
    time_table = {'航空港校区': [None] * 12, '龙泉校区': [None] * 12}

if CAMPUS not in time_table:
    CAMPUS = '航空港校区'
period_times = time_table.get(CAMPUS, [None] * 12)

# ==================== 原有工具函数（基于本地文件，备用） ====================
@tool
def query_schedule(weekday: str, period: Optional[str] = None, week: Optional[int] = None, campus: Optional[str] = None) -> str:
    """
    【备用工具】查询本地缓存的课表。
    """
    wk_map = {
        '周一': '周一', '周二': '周二', '周三': '周三', '周四': '周四', '周五': '周五', '周六': '周六', '周日': '周日',
        '星期一': '周一', '星期二': '周二', '星期三': '周三', '星期四': '周四', '星期五': '周五', '星期六': '周六', '星期日': '周日'
    }
    weekday_std = wk_map.get(weekday, weekday)
    if weekday_std not in weekday_map:
        return f"无法识别星期：{weekday}"
    day_idx = weekday_map[weekday_std]

    target_week = week if week is not None else get_current_week()
    if target_week <= 0:
        return f"当前日期早于学期开始日期，无法查询课表。"

    use_campus = campus if campus and campus in time_table else CAMPUS
    times = time_table.get(use_campus, time_table.get('航空港校区', [None] * 12))

    def is_week_in_course(weeks_text: str, week_num: int) -> bool:
        if not weeks_text:
            return False
        parts = weeks_text.strip().split('-')
        if len(parts) == 1:
            try:
                return int(parts[0]) == week_num
            except:
                return False
        elif len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return start <= week_num <= end
            except:
                return False
        return False

    if period is None or period == '全天':
        lines = [f"{weekday_std}全天课程（第{target_week}周，{use_campus}时间）："]
        has_any = False
        for p_idx, p_name in enumerate(period_names):
            act = schedule_matrix[day_idx][p_idx]
            time_str = ""
            if times and p_idx < len(times) and times[p_idx]:
                start, end = times[p_idx]
                time_str = f"（{start.strftime('%H:%M')}-{end.strftime('%H:%M')}）"
            if act:
                if is_week_in_course(act.get('weeks_text', ''), target_week):
                    has_any = True
                    lines.append(f"{p_name}{time_str}：{act['course_name']}（{act['teacher']}）@{act['classroom']}，本周有课")
                else:
                    lines.append(f"{p_name}{time_str}：{act['course_name']}，但本周无课")
            else:
                lines.append(f"{p_name}{time_str}：无课")
        if not has_any:
            lines.append("（本周该日无任何课程安排）")
        return "\n".join(lines)
    else:
        if period not in period_names:
            return f"无法识别节次：{period}"
        p_idx = period_names.index(period)
        act = schedule_matrix[day_idx][p_idx]
        if act:
            if is_week_in_course(act.get('weeks_text', ''), target_week):
                return f"{weekday_std}{period}：{act['course_name']}（{act['teacher']}）@{act['classroom']}，本周有课"
            else:
                return f"{weekday_std}{period}：{act['course_name']}，但本周无课"
        return f"{weekday_std}{period}：无课程安排"

@tool
def query_grades(course_name: Optional[str] = None, show_stats: bool = False) -> str:
    """
    【备用工具】查询本地缓存的成绩。
    """
    if not grade_courses:
        return "成绩数据未加载"
    if course_name:
        matches = [g for g in grade_courses if course_name in g['course_name']]
        if not matches:
            return f"未找到包含'{course_name}'的课程"
        return "\n".join(
            f"{g['course_name']}：总评 {g['total_score']}，绩点 {g['gpa']}"
            for g in matches
        )
    else:
        if show_stats:
            stats = grade_stats
            return (f"成绩统计：\n总课程数：{stats.get('total_courses', 0)}\n"
                    f"总学分：{stats.get('total_credits', 0)}\n"
                    f"平均绩点：{stats.get('avg_gpa', 0)}\n"
                    f"平均分：{stats.get('avg_score', 0)}")
        else:
            lines = ["所有课程成绩："]
            for g in grade_courses:
                lines.append(f"{g['course_name']}：{g['total_score']}分，绩点{g['gpa']}")
            return "\n".join(lines)

@tool
def query_course_list() -> str:
    """列出本学期所有课程（基于本地缓存文件）"""
    if not course_list:
        return "课程列表未加载"
    lines = ["本学期课程列表："]
    for c in course_list:
        lines.append(f"  • {c['name']}（{c['code']}），学分{c['credit']}，教师{c['teacher']}")
    return "\n".join(lines)

@tool
def query_current_week() -> str:
    """查询当前是学期第几周"""
    week_num = get_current_week()
    if week_num <= 0:
        return f"学期尚未开始（开始日期：{SEMESTER_START}）"
    return f"当前是学期第 {week_num} 周"

@tool
def query_current_time() -> str:
    """返回当前日期、时间和学期周次"""
    now = datetime.now()
    weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()]
    week_num = get_current_week()
    return f"现在是 {now.strftime('%Y年%m月%d日 %H:%M:%S')}，{weekday_cn}，学期第 {week_num} 周"

@tool
def query_current_course(campus: Optional[str] = None) -> str:
    """根据当前时间判断现在正在上什么课（基于本地缓存）"""
    use_campus = campus if campus and campus in time_table else CAMPUS
    times = time_table.get(use_campus, time_table.get('航空港校区', [None] * 12))
    
    now = datetime.now()
    day_idx = now.weekday()
    current_time = now.time()
    current_week = get_current_week()
    
    if current_week <= 0:
        return f"学期尚未开始，无法查询实时课程"
    
    def has_course_in_week(weeks_binary: str, week_num: int) -> bool:
        if not weeks_binary or week_num < 1 or week_num > len(weeks_binary):
            return False
        return weeks_binary[week_num - 1] == '1'
    
    current_period = None
    for i, (start, end) in enumerate(times):
        if start and start <= current_time <= end:
            current_period = i
            break
    
    next_period = None
    if current_period is None:
        for i, (start, end) in enumerate(times):
            if start and start > current_time:
                next_period = i
                break
    
    if current_period is not None:
        act = schedule_matrix[day_idx][current_period] if day_idx < len(schedule_matrix) else None
        period_name = period_names[current_period]
        if act and has_course_in_week(act.get('weeks_binary', ''), current_week):
            return f"当前正在上：{period_name} {act['course_name']}（{act['teacher']}）@{act['classroom']}"
        else:
            return f"当前{period_name}无课程安排"
    
    elif next_period is not None:
        act = schedule_matrix[day_idx][next_period] if day_idx < len(schedule_matrix) else None
        period_name = period_names[next_period]
        if act and has_course_in_week(act.get('weeks_binary', ''), current_week):
            return f"下一节课是{period_name}：{act['course_name']}（{act['teacher']}）@{act['classroom']}"
        else:
            return f"下一节{period_name}无课程安排"
    else:
        return "今天没有更多课程了"

# ==================== 导出工具列表 ====================
# 原有工具（基于本地文件）
local_tools = [query_schedule, query_grades, query_course_list, query_current_week, query_current_course, query_current_time]

# 实时爬虫工具（需要登录）
live_tools = [fetch_live_courses, fetch_live_grades, fetch_live_current_course, fetch_live_exams]

# 合并所有工具
tools = local_tools + live_tools
tools_by_name = {tool.name: tool for tool in tools}