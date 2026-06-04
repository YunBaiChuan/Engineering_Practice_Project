import requests
import sys 
import os
import time
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import settings
from bs4 import BeautifulSoup

class CUITCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        
        self.ywtb_url = "https://ywtb.cuit.edu.cn"
        self.jwgl_url = settings.JWGL_URL
    
    def login(self, username=None, password=None):
        """完整登录流程"""
        username = username or settings.STUDENT_ID
        password = password or settings.PASSWORD
        
        # 第一步：登录一站式平台
        url = f"{self.ywtb_url}/api/base/login"
        payload = {
            "username": username,
            "password": password,
            "validateCode": "",
            "loginType": "cas",
            "redirectUrl": "http://jwgl.cuit.edu.cn/eams/"
        }
        
        resp = self.session.post(url, json=payload)
        result = resp.json()
        
        if result.get('msg') != '操作成功':
            print(f"登录失败: {result}")
            return False
        
        print(f"登录成功: {result['data']['userName']}")
        
        # 第二步：访问 CAS 获取跳转页面
        redirect_uri = result.get('redirect_uri')
        if redirect_uri:
            print(f"访问CAS: {redirect_uri}")
            cas_resp = self.session.get(redirect_uri, allow_redirects=True)
            print(f"CAS状态码: {cas_resp.status_code}")
            
            # 从返回的HTML中提取跳转URL
            soup = BeautifulSoup(cas_resp.text, 'html.parser')
            jump_link = soup.find('a', id='jump')
            
            if jump_link and jump_link.get('href'):
                ticket_url = jump_link['href']
                print(f"提取到Ticket URL: {ticket_url}")
                
                # 关键：访问带 Ticket 的 URL
                print("正在跳转...")
                final_resp = self.session.get(ticket_url, allow_redirects=True)
                print(f"最终状态: {final_resp.status_code}")
                print(f"最终URL: {final_resp.url}")
                print(f"最终Cookies: {self.session.cookies.get_dict()}")
                
                # 检查是否成功进入教务系统
                if 'jwgl.cuit.edu.cn' in final_resp.url and 'login' not in final_resp.url:
                    print("✅ 成功进入教务系统")
                    return True
        
        print("❌ 登录流程未完成")
        return False
    
    def get_course_table(self):
        """获取课表（在已登录状态下）"""
        # 先访问入口页（确保会话有效，并获取隐藏字段）
        entry_url = f"{self.jwgl_url}/courseTableForStd.action"
        entry_resp = self.session.get(entry_url, allow_redirects=True)
        
        print(f"入口页状态码: {entry_resp.status_code}")
        print(f"入口页URL: {entry_resp.url}")
        print(f"入口页长度: {len(entry_resp.text)}")
        
        # 如果被重定向，说明 Cookie 问题
        if 'login' in entry_resp.url or 'authserver' in entry_resp.url:
            print("❌ Cookie失效，被重定向到登录页")
            return entry_resp.text
        
        # 检查是否直接包含课表
        if '课程列表' in entry_resp.text and len(entry_resp.text) > 5000:
            print("✅ 入口页包含课表数据")
            return entry_resp.text
        
        # 从入口页提取 semester.id
        soup = BeautifulSoup(entry_resp.text, 'html.parser')
        semester_input = soup.find('input', {'name': 'semester.id'})
        semester_id = semester_input['value'] if semester_input else '1006'
        
        # 提取 ids
        ids = '203787'
        for script in soup.find_all('script'):
            text = script.string or ''
            if 'ids' in text:
                match = re.search(r'ids[=:]["\']?(\d+)["\']?', text)
                if match:
                    ids = match.group(1)
                    break
        
        # POST 获取课表数据（模拟 searchTable）
        url = f"{self.jwgl_url}/courseTableForStd!courseTable.action"
        data = {
            "ignoreHead": "1",
            "setting.kind": "std",
            "ids": ids,
            "startWeek": "",
            "semester.id": semester_id
        }
        
        headers = {
            'Referer': entry_url,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        resp = self.session.post(url, data=data, headers=headers, allow_redirects=True)
        print(f"课表状态码: {resp.status_code}")
        print(f"课表URL: {resp.url}")
        print(f"课表长度: {len(resp.text)}")
        
        # 检查内容
        if '课程列表' in resp.text:
            print("✅ 包含课程列表")
        elif 'error' in resp.text.lower():
            print("❌ 包含错误信息")
        else:
            print(f"内容片段: {resp.text[:500]}")
        
        return resp.text

    def get_grade_table(self, semester_id=None):
        """获取成绩表（在已登录状态下）"""
        semester_id = semester_id or '906'
        
        entry_url = f"{self.jwgl_url}/teach/grade/course/person!search.action"
        entry_params = {
            'semesterId': semester_id,
            'projectType': ''
        }
        
        entry_resp = self.session.get(entry_url, params=entry_params, allow_redirects=True)
        
        print(f"成绩入口页状态码: {entry_resp.status_code}")
        print(f"成绩入口页URL: {entry_resp.url}")
        print(f"成绩入口页长度: {len(entry_resp.text)}")
        
        if 'login' in entry_resp.url or 'authserver' in entry_resp.url:
            print("❌ Cookie失效，被重定向到登录页")
            return entry_resp.text
        
        if 'gridtable' in entry_resp.text and '总评成绩' in entry_resp.text:
            print("✅ 入口页包含成绩数据")
            return entry_resp.text
        
        soup = BeautifulSoup(entry_resp.text, 'html.parser')
        
        grid_params = {}
        for script in soup.find_all('script'):
            text = script.string or ''
            match = re.search(r"_paramstring\s*=\s*'([^']+)'", text)
            if match:
                param_string = match.group(1)
                for param in param_string.split('&'):
                    if '=' in param:
                        k, v = param.split('=', 1)
                        grid_params[k] = v
                break
        
        url = f"{self.jwgl_url}/teach/grade/course/person!search.action"
        params = {
            'semesterId': semester_id,
            'projectType': '',
            '_': str(int(time.time() * 1000))
        }
        params.update(grid_params)
        
        headers = {
            'Referer': entry_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'text/html, */*; q=0.01'
        }
        
        resp = self.session.get(url, params=params, headers=headers, allow_redirects=True)
        print(f"成绩状态码: {resp.status_code}")
        print(f"成绩URL: {resp.url}")
        print(f"成绩长度: {len(resp.text)}")
        
        if 'gridtable' in resp.text:
            print("✅ 包含成绩列表")
        elif 'error' in resp.text.lower():
            print("❌ 包含错误信息")
        else:
            print(f"内容片段: {resp.text[:500]}")
        
        return resp.text

    def get_exam_table(self, exam_batch_id='5228'):
        """
        获取考试安排表（在已登录状态下）
        
        Args:
            exam_batch_id: 考试批次ID，默认5228（根据实际页面获取）
        
        Returns:
            考试安排的HTML内容
        """
        # 先访问入口页获取参数
        entry_url = f"{self.jwgl_url}/stdExamTable!examTable.action"
        entry_params = {
            'examBatch.id': exam_batch_id
        }
        
        entry_resp = self.session.get(entry_url, params=entry_params, allow_redirects=True)
        print(f"考试入口页状态码: {entry_resp.status_code}")
        print(f"考试入口页URL: {entry_resp.url}")
        print(f"考试入口页长度: {len(entry_resp.text)}")
        
        if 'login' in entry_resp.url or 'authserver' in entry_resp.url:
            print("❌ Cookie失效，被重定向到登录页")
            return entry_resp.text
        
        # 从返回的HTML中提取grid参数
        soup = BeautifulSoup(entry_resp.text, 'html.parser')
        
        # 提取grid参数（从JavaScript中）
        grid_params = {}
        for script in soup.find_all('script'):
            text = script.string or ''
            # 查找 _paramstring 变量
            match = re.search(r"_paramstring\s*=\s*'([^']+)'", text)
            if match:
                param_string = match.group(1)
                for param in param_string.split('&'):
                    if '=' in param:
                        k, v = param.split('=', 1)
                        grid_params[k] = v
                break
        
        # 如果有参数，直接请求数据接口
        url = f"{self.jwgl_url}/stdExamTable!examTable.action"
        params = {
            'examBatch.id': exam_batch_id,
            '_': str(int(time.time() * 1000))
        }
        params.update(grid_params)
        
        headers = {
            'Referer': entry_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'text/html, */*; q=0.01'
        }
        
        resp = self.session.get(url, params=params, headers=headers, allow_redirects=True)
        print(f"考试状态码: {resp.status_code}")
        print(f"考试URL: {resp.url}")
        print(f"考试长度: {len(resp.text)}")
        
        if 'gridtable' in resp.text:
            print("✅ 包含考试列表")
        elif 'error' in resp.text.lower():
            print("❌ 包含错误信息")
        else:
            print(f"内容片段: {resp.text[:500]}")
        
        return resp.text
    
    def get_session(self):
        """返回session供其他模块使用"""
        return self.session

# 测试
if __name__ == "__main__":
    cuitCrawler = CUITCrawler()

    print()
    print("=" * 100)
    print()

    status = cuitCrawler.login()
    
    print()
    print("=" * 100)
    print()
    
    if status:
        # 测试爬取课表
        html = cuitCrawler.get_course_table()
        with open('course_table.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n课表已保存，长度: {len(html)}")
        
        # 测试爬取成绩
        html = cuitCrawler.get_grade_table()
        with open('grade_table.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n成绩已保存，长度: {len(html)}")
        
        # 测试爬取考试安排
        print()
        print("=" * 100)
        print("开始爬取考试安排")
        print("=" * 100)
        
        exam_html = cuitCrawler.get_exam_table(exam_batch_id='5228')
        with open('exam_table.html', 'w', encoding='utf-8') as f:
            f.write(exam_html)
        print(f"\n考试安排已保存，长度: {len(exam_html)}")