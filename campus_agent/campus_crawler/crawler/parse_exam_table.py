import re
from bs4 import BeautifulSoup

def parse_exam_table(html):
    """
    解析考试安排HTML
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找考试表格
    table = soup.find('table', class_=re.compile(r'gridtable'))
    exams = []
    
    if table and table.find('tbody'):
        for row in table.find('tbody').find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 9:
                # 提取考试信息
                course_code = cols[0].get_text(strip=True) if cols[0] else ''
                course_name = cols[1].get_text(strip=True) if cols[1] else ''
                exam_type = cols[2].get_text(strip=True) if cols[2] else ''
                
                # 考试日期、时间、地点（处理font标签）
                exam_date = extract_text_safe(cols[3])
                exam_time = extract_text_safe(cols[4])
                exam_location = extract_text_safe(cols[5])
                
                credit = cols[6].get_text(strip=True) if cols[6] else ''
                status = cols[7].get_text(strip=True) if cols[7] else ''
                remark = cols[8].get_text(strip=True) if cols[8] else ''
                
                exams.append({
                    'course_code': course_code,
                    'course_name': course_name,
                    'exam_type': exam_type,
                    'exam_date': exam_date,
                    'exam_time': exam_time,
                    'exam_location': exam_location,
                    'credit': credit,
                    'status': status,
                    'remark': remark
                })
    
    # 统计信息
    total_exams = len(exams)
    scheduled_exams = sum(1 for e in exams if e['exam_date'] and '未安排' not in e['exam_date'])
    unscheduled_exams = total_exams - scheduled_exams
    
    stats = {
        'total_exams': total_exams,
        'scheduled_exams': scheduled_exams,
        'unscheduled_exams': unscheduled_exams
    }
    
    return {
        'exams': exams,
        'stats': stats
    }

def extract_text_safe(element):
    """
    安全提取文本，正确处理font标签，避免出现删除线样式
    """
    if element is None:
        return ''
    
    # 复制元素，避免修改原始数据
    element_copy = element.__copy__()
    
    # 处理所有font标签，提取其中的文本
    for font in element_copy.find_all('font'):
        text = font.get_text(strip=True)
        font.replace_with(text)
    
    # 处理链接标签
    for link in element_copy.find_all('a'):
        text = link.get_text(strip=True)
        link.replace_with(text)
    
    # 获取纯文本
    text = element_copy.get_text(strip=True)
    
    # 清理多余空格和特殊字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 如果文本包含"未安排"，返回友好提示
    if '未安排' in text or '未安排' in text:
        return '待定'
    
    return text

# 测试
if __name__ == "__main__":
    with open('data/exam_table.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    result = parse_exam_table(html)
    
    print(f"考试数量: {len(result['exams'])}")
    print(f"已安排: {result['stats']['scheduled_exams']}")
    print(f"未安排: {result['stats']['unscheduled_exams']}")
    print("\n考试明细:")
    print("-" * 100)
    
    for exam in result['exams']:
        print(f"{exam['course_name']} | {exam['exam_type']} | {exam['exam_date']} | {exam['exam_time']} | {exam['exam_location']}")