import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from typing import AsyncGenerator, List, Dict, Any
import json
from datetime import datetime, timedelta

from agent.tools import tools, tools_by_name, fetch_live_courses, fetch_live_grades, fetch_live_current_course
from agent.memory import get_memory

load_dotenv()

SYSTEM_PROMPT = """你是成都信息工程大学的校园信息查询助手。用户已登录，你可以帮助用户查询课表、成绩等信息。

你有记忆功能，可以记住用户告诉你的信息（如名字、偏好等）。在后续对话中，你可以使用这些信息来提供更个性化的服务。

注意：历史对话已经提供给你，请参考历史对话中的信息来回答用户问题。"""

def create_agent():
    """创建并返回LangGraph Agent"""
    llm = ChatOpenAI(
        model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
        openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
        openai_api_base=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        temperature=0
    ).bind_tools(tools)

    def agent_node(state: MessagesState) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    def tools_node(state: MessagesState) -> dict:
        last = state["messages"][-1]
        tool_msgs = []
        for tc in last.tool_calls:
            tool_func = tools_by_name[tc["name"]]
            result = tool_func.invoke(tc["args"])
            tool_msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        return {"messages": tool_msgs}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    
    return builder.compile()

# 创建全局agent实例
agent = create_agent()

def chat(message: str, history: list = None) -> str:
    """简单的对话接口"""
    if history is None:
        history = []
    
    result = agent.invoke({"messages": history + [HumanMessage(content=message)]})
    
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return "抱歉，我无法处理这个请求。"

# ========== 星期常量 ==========
weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

def get_weekday_from_message(message: str) -> tuple:
    """
    从消息中提取星期几
    返回 (weekday, days_offset)
    """
    # 今天
    if '今天' in message:
        return weekdays[datetime.now().weekday()], 0
    # 明天
    if '明天' in message:
        tomorrow = datetime.now() + timedelta(days=1)
        return weekdays[tomorrow.weekday()], 1
    # 后天
    if '后天' in message:
        day_after = datetime.now() + timedelta(days=2)
        return weekdays[day_after.weekday()], 2
    # 大后天
    if '大后天' in message:
        day_after_after = datetime.now() + timedelta(days=3)
        return weekdays[day_after_after.weekday()], 3
    # 昨天
    if '昨天' in message:
        yesterday = datetime.now() - timedelta(days=1)
        return weekdays[yesterday.weekday()], -1
    
    # 具体星期
    weekday_map = {
        '周一': '周一', '星期一': '周一',
        '周二': '周二', '星期二': '周二',
        '周三': '周三', '星期三': '周三',
        '周四': '周四', '星期四': '周四',
        '周五': '周五', '星期五': '周五',
        '周六': '周六', '星期六': '周六',
        '周日': '周日', '星期日': '周日'
    }
    for key, value in weekday_map.items():
        if key in message:
            return value, None
    
    return None, None

def detect_intent_and_call_tool(message: str, user_info: Dict = None) -> tuple:
    """
    检测用户意图，直接调用工具
    返回 (是否处理, 结果内容)
    """
    if not user_info or not user_info.get('username') or not user_info.get('password'):
        return False, None
    
    username = user_info['username']
    password = user_info['password']
    msg_lower = message.lower()
    
    # 先判断是否有指定日期（周一~周日）
    has_specific_weekday = any(x in message for x in ['周一', '周二', '周三', '周四', '周五', '周六', '周日',
                                                       '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'])
    has_today_tomorrow = any(x in message for x in ['今天', '明天', '后天', '大后天'])
    
    # ==================== 0. 处理用户告知姓名和询问姓名 ====================
    import re
    
    # 先处理询问姓名（排除"我叫什么"这种问句）
    ask_name_patterns = ['我叫什么', '我叫啥', '我是谁', '你记得我吗', '你知道我叫什么吗', '我的名字']
    if any(kw in message for kw in ask_name_patterns):
        memory = get_memory()
        if user_info and user_info.get('username'):
            name = memory.get_user_info(user_info['username'], "name")
            if name:
                return True, f"你是{name}同学呀！"
            else:
                return True, "你还告诉我你的名字呢。你可以说'我叫XXX'告诉我。"
        return True, "你还告诉我你的名字呢。你可以说'我叫XXX'告诉我。"
    
    # 再处理告知姓名（必须是"我叫XXX"格式，且名字不能是"什么"）
    tell_name_patterns = [
        r'我叫([\u4e00-\u9fa5a-zA-Z]+)',
        r'我是([\u4e00-\u9fa5a-zA-Z]+)',
        r'名字叫([\u4e00-\u9fa5a-zA-Z]+)',
        r'姓名是([\u4e00-\u9fa5a-zA-Z]+)',
    ]
    
    for pattern in tell_name_patterns:
        match = re.search(pattern, message)
        if match:
            name = match.group(1)
            # 过滤掉"什么"这种无效名字
            if name == '什么' or len(name) > 20:
                continue
            # 保存到记忆
            memory = get_memory()
            if user_info and user_info.get('username'):
                memory.set_user_info(user_info['username'], "name", name)
            return True, f"你好！{name}同学。请问有什么可以帮你的吗？"
    
    # ==================== 1. 优先处理指定日期的课表查询 ====================
    if has_specific_weekday or has_today_tomorrow:
        weekday, offset = get_weekday_from_message(message)
        
        if weekday is not None:
            try:
                result = fetch_live_courses.invoke({
                    'username': username,
                    'password': password,
                    'weekday': weekday
                })
                return True, result
            except Exception as e:
                return True, f"❌ 获取课表失败：{str(e)}"
    
    # ==================== 2. 课程列表查询（没有指定日期时） ====================
    course_list_keywords = ['这学期', '有哪些课程', '全部课程', '所有课程', '课程列表', '学了哪些']
    if any(kw in msg_lower for kw in course_list_keywords):
        try:
            result = fetch_live_courses.invoke({
                'username': username,
                'password': password,
                'weekday': None
            })
            return True, result
        except Exception as e:
            return True, f"❌ 获取课程列表失败：{str(e)}"
    
    # ==================== 3. 本周课表查询 ====================
    if '这周' in msg_lower or '本周' in msg_lower:
        try:
            result = fetch_live_courses.invoke({
                'username': username,
                'password': password,
                'weekday': None
            })
            return True, result
        except Exception as e:
            return True, f"❌ 获取本周课表失败：{str(e)}"
    
    # ==================== 4. 通用课表查询（兜底） ====================
    course_keywords = [
        '课表', '有什么课', '什么课', '有课吗', '有课没',
        '下午有课', '上午有课', '几节课'
    ]
    if any(kw in msg_lower for kw in course_keywords):
        weekday, offset = get_weekday_from_message(message)
        
        if weekday is None:
            try:
                result = fetch_live_courses.invoke({
                    'username': username,
                    'password': password,
                    'weekday': None
                })
                return True, result
            except Exception as e:
                return True, f"❌ 获取课程列表失败：{str(e)}"
        else:
            try:
                result = fetch_live_courses.invoke({
                    'username': username,
                    'password': password,
                    'weekday': weekday
                })
                return True, result
            except Exception as e:
                return True, f"❌ 获取课表失败：{str(e)}"
    
    # ==================== 5. 成绩查询 ====================
    grade_keywords = ['成绩', '考了', '分数', '绩点', '平均分', '平均绩点']
    if any(kw in msg_lower for kw in grade_keywords):
        try:
            result = fetch_live_grades.invoke({
                'username': username,
                'password': password
            })
            return True, result
        except Exception as e:
            return True, f"❌ 获取成绩失败：{str(e)}"
    
    # ==================== 6. 当前课程查询 ====================
    current_course_keywords = ['现在上什么课', '当前课程', '正在上', '下一节', '等会儿有课', '待会儿有课']
    if any(kw in msg_lower for kw in current_course_keywords):
        try:
            result = fetch_live_current_course.invoke({
                'username': username,
                'password': password
            })
            return True, result
        except Exception as e:
            return True, f"❌ 获取当前课程失败：{str(e)}"
    
    # ==================== 7. 时间/周次查询 ====================
    if '第几周' in msg_lower or '当前周' in msg_lower:
        from utils.week_utils import get_current_week, SEMESTER_START
        week_num = get_current_week()
        if week_num <= 0:
            return True, f"学期尚未开始（开始日期：{SEMESTER_START}）"
        return True, f"当前是学期第 {week_num} 周"
    
    if '几点' in msg_lower or '现在时间' in msg_lower or '当前时间' in msg_lower:
        now = datetime.now()
        weekday_cn = weekdays[now.weekday()]
        return True, f"现在是 {now.strftime('%Y年%m月%d日 %H:%M:%S')}，{weekday_cn}"
    
    return False, None

# ========== 流式对话接口（支持工具调用和记忆） ==========
async def stream_chat(message: str, history: List[Dict] = None, user_info: Dict = None) -> AsyncGenerator[str, None]:
    """
    流式对话接口 - 完整支持工具调用和记忆
    """
    user_id = user_info.get('username') if user_info else None
    
    if not user_id:
        user_id = "anonymous"
    
    memory = get_memory()
    
    # 先尝试意图识别和直接工具调用
    handled, tool_result = detect_intent_and_call_tool(message, user_info)
    
    if handled:
        # 保存到记忆
        memory.add_message(user_id, "user", message)
        memory.add_message(user_id, "assistant", tool_result)
        yield tool_result
        return
    
    # 构建系统提示
    system_prompt = """你是成都信息工程大学的校园信息查询助手。帮助用户回答一般性问题。

请参考【历史对话】中的内容来回答用户问题，保持对话的连贯性。如果用户之前告诉过你他的名字或其他信息，请在回答中使用这些信息。"""
    
    # 获取用户信息
    user_name = memory.get_user_info(user_id, "name")
    if user_name:
        system_prompt += f"\n\n用户姓名：{user_name}，你可以用这个名字称呼用户。"
    
    # 获取对话历史
    conversation_history = memory.get_history(user_id, max_turns=10)
    
    # 构建消息列表
    messages = [SystemMessage(content=system_prompt)]
    
    # 添加历史对话
    for msg in conversation_history:
        if msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(AIMessage(content=msg['content']))
    
    # 添加当前消息
    messages.append(HumanMessage(content=message))
    
    # 保存用户消息到记忆
    memory.add_message(user_id, "user", message)
    
    # 调用LLM
    llm = ChatOpenAI(
        model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
        openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
        openai_api_base=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        temperature=0.7,
        streaming=True
    )
    
    full_response = ""
    async for chunk in llm.astream(messages):
        if chunk.content:
            full_response += chunk.content
            yield chunk.content
    
    # 保存助手回复到记忆
    if full_response:
        memory.add_message(user_id, "assistant", full_response)

# 命令行交互（流式版）
async def interactive_chat_stream():
    print("校园信息查询助手已启动（流式版，带记忆）。输入问题（或'退出'结束）")
    user_id = "cli_user"
    
    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ["退出", "exit", "quit"]:
            print("再见！")
            break
        
        print("助手: ", end='', flush=True)
        
        async for chunk in stream_chat(user_input, None, {"username": user_id, "password": ""}):
            print(chunk, end='', flush=True)
        
        print()

# 命令行交互（非流式）
def interactive_chat():
    print("校园信息查询助手已启动。输入问题（或'退出'结束）")
    history = []
    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ["退出", "exit", "quit"]:
            print("再见！")
            break
        
        result = agent.invoke({"messages": history + [HumanMessage(content=user_input)]})
        history = result["messages"]
        
        for msg in reversed(history):
            if isinstance(msg, AIMessage) and msg.content:
                print(f"助手: {msg.content}")
                break

if __name__ == "__main__":
    import asyncio
    asyncio.run(interactive_chat_stream())