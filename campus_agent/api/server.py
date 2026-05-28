from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import logging
import hashlib
import json
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph_agent import create_agent, stream_chat
from langchain_core.messages import HumanMessage, AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="Campus Agent API", description="校园智能助手后端")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 数据库配置 ==========
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'campus_agent_db'),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        return None

# ========== 请求模型 ==========
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    user_info: Optional[dict] = None  # 新增：用户信息字段

class CourseRequest(BaseModel):
    weekday: str = "周一"
    period: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: Optional[str] = None

# ========== 全局 Agent ==========
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent

def hash_password(password: str) -> str:
    """密码加密"""
    return hashlib.sha256(password.encode()).hexdigest()

# ========== 流式响应生成器 ==========
async def stream_generator(message: str, history: List[dict] = None, user_info: dict = None):
    """生成流式响应 - 使用 Agent 的流式接口"""
    try:
        # 使用 agent 的流式聊天函数，传递 user_info
        async for chunk in stream_chat(message, history, user_info):
            if chunk:
                # 发送 SSE 格式的数据
                yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"
        
        # 发送完成标记
        yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        logger.error(f"流式生成失败: {e}")
        error_msg = f"服务暂时不可用: {str(e)}"
        yield f"data: {json.dumps({'content': error_msg, 'done': True}, ensure_ascii=False)}\n\n"

# ========== 路由 ==========
@app.get("/api/health")
def health_check():
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    if conn:
        conn.close()
    return {
        "code": 200, 
        "status": "ok", 
        "message": "Campus Agent Running",
        "database": db_status
    }

# 普通聊天接口（非流式）- 也支持 user_info
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        logger.info(f"收到消息: {request.message}")
        
        agent = get_agent()
        # 如果有 user_info，可以添加到消息中
        messages = [{"role": "user", "content": request.message}]
        result = agent.invoke({"messages": messages})
        
        response_text = ""
        for msg in reversed(result["messages"]):
            if hasattr(msg, 'content') and msg.content:
                response_text = msg.content
                break
        
        return {"code": 200, "data": {"response": response_text}}
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 流式聊天接口
@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口 - 支持打字机效果和工具调用"""
    logger.info(f"流式收到消息: {request.message}")
    if request.user_info:
        logger.info(f"用户: {request.user_info.get('username', 'unknown')}")
    
    return StreamingResponse(
        stream_generator(request.message, request.history, request.user_info),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/courses")
async def get_courses(request: CourseRequest):
    try:
        from agent.tools import query_schedule
        result = query_schedule.invoke({
            "weekday": request.weekday,
            "period": request.period
        })
        return {"code": 200, "data": {"result": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/grades")
async def get_grades(course_name: Optional[str] = None, show_stats: bool = False):
    try:
        from agent.tools import query_grades
        result = query_grades.invoke({
            "course_name": course_name,
            "show_stats": show_stats
        })
        return {"code": 200, "data": {"result": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 登录/注册接口 ==========
@app.post("/api/login")
async def login(request: LoginRequest):
    """用户登录 - MySQL"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT id, username, name, status, password FROM users WHERE username = %s",
            (request.username,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="学号或密码错误")
        
        if user.get('status') != 1:
            raise HTTPException(status_code=401, detail="账号已被禁用")
        
        if user['password'] != hash_password(request.password):
            raise HTTPException(status_code=401, detail="学号或密码错误")
        
        cursor.execute(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (datetime.now(), user['id'])
        )
        conn.commit()
        
        # 注意：这里不返回密码，只返回用户基本信息
        return {
            "code": 200,
            "message": "登录成功",
            "data": {
                "id": user['id'],
                "username": user['username'],
                "name": user['name'],
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.post("/api/register")
async def register(request: RegisterRequest):
    """用户注册 - MySQL"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id FROM users WHERE username = %s", (request.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户已存在")
        
        cursor.execute(
            """INSERT INTO users (username, password, name, created_at) 
               VALUES (%s, %s, %s, %s)""",
            (
                request.username,
                hash_password(request.password),
                request.name or request.username,
                datetime.now()
            )
        )
        conn.commit()
        
        return {
            "code": 200,
            "message": "注册成功",
            "data": {
                "username": request.username,
                "name": request.name or request.username
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.post("/api/logout")
async def logout():
    """用户登出"""
    return {
        "code": 200,
        "message": "登出成功"
    }

# ========== 启动 ==========
if __name__ == '__main__':
    import uvicorn
    
    print("=" * 60)
    print("🚀 Campus Agent FastAPI 服务启动 (MySQL + 流式)")
    print("📍 地址: http://localhost:5000")
    print("📋 API 文档: http://localhost:5000/docs")
    print("🗄️  数据库: campus_agent_db -> users")
    print("=" * 60)
    
    uvicorn.run(app, host='0.0.0.0', port=5000)