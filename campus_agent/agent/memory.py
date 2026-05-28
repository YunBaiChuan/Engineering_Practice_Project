from datetime import datetime
from typing import List, Dict, Optional
import json
import os

class ConversationMemory:
    """对话记忆管理器"""
    
    def __init__(self, max_history: int = 20):
        """
        初始化记忆管理器
        
        Args:
            max_history: 最多保留的对话条数
        """
        self.max_history = max_history
        self._sessions = {}  # {user_id: {"messages": [], "user_info": {}}}
    
    def get_session(self, user_id: str) -> dict:
        """获取用户会话"""
        if user_id not in self._sessions:
            self._sessions[user_id] = {
                "messages": [],      # 对话历史
                "user_info": {},     # 用户信息（姓名等）
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
        return self._sessions[user_id]
    
    def add_message(self, user_id: str, role: str, content: str):
        """
        添加消息到记忆
        
        Args:
            user_id: 用户ID
            role: 角色 (user, assistant, system)
            content: 消息内容
        """
        session = self.get_session(user_id)
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session["last_active"] = datetime.now().isoformat()
        
        # 保持最大长度
        if len(session["messages"]) > self.max_history * 2:
            session["messages"] = session["messages"][-self.max_history * 2:]
    
    def get_history(self, user_id: str, max_turns: int = None) -> List[Dict]:
        """
        获取对话历史
        
        Args:
            user_id: 用户ID
            max_turns: 最多返回多少轮对话（一轮 = 用户+助手）
        
        Returns:
            消息列表，格式适合发送给LLM
        """
        session = self.get_session(user_id)
        messages = session["messages"]
        
        if max_turns:
            # 每轮2条消息（用户+助手），所以限制条数
            limit = max_turns * 2
            messages = messages[-limit:]
        
        # 返回适合LLM的格式（不包含timestamp）
        return [{"role": m["role"], "content": m["content"]} for m in messages]
    
    def set_user_info(self, user_id: str, key: str, value: str):
        """存储用户信息（如姓名）"""
        session = self.get_session(user_id)
        session["user_info"][key] = value
    
    def get_user_info(self, user_id: str, key: str = None):
        """获取用户信息"""
        session = self.get_session(user_id)
        if key:
            return session["user_info"].get(key)
        return session["user_info"]
    
    def clear_history(self, user_id: str):
        """清空对话历史"""
        session = self.get_session(user_id)
        session["messages"] = []
    
    def build_context_prompt(self, user_id: str, max_turns: int = 5) -> str:
        """
        构建上下文提示词
        
        Args:
            user_id: 用户ID
            max_turns: 最多包含多少轮对话
        
        Returns:
            格式化的上下文字符串
        """
        history = self.get_history(user_id, max_turns)
        if not history:
            return ""
        
        context_lines = ["【历史对话】"]
        for msg in history:
            role = "用户" if msg["role"] == "user" else "助手"
            context_lines.append(f"{role}: {msg['content']}")
        context_lines.append("【以上是历史对话】")
        
        return "\n".join(context_lines)
    
    def get_user_context(self, user_id: str) -> str:
        """获取用户上下文（姓名等）"""
        user_info = self.get_user_info(user_id)
        if not user_info:
            return ""
        
        context_parts = []
        if user_info.get("name"):
            context_parts.append(f"用户姓名：{user_info['name']}")
        
        if context_parts:
            return f"【用户信息】\n" + "\n".join(context_parts) + "\n"
        return ""


# ========== 全局记忆实例 ==========
_memory = None

def get_memory() -> ConversationMemory:
    """获取全局记忆实例（单例）"""
    global _memory
    if _memory is None:
        _memory = ConversationMemory(max_history=20)
    return _memory


# ========== 记忆持久化（可选） ==========
def save_memory_to_file(filepath: str = "data/memory.json"):
    """保存记忆到文件"""
    memory = get_memory()
    data = {
        "sessions": memory._sessions,
        "saved_at": datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_memory_from_file(filepath: str = "data/memory.json"):
    """从文件加载记忆"""
    if not os.path.exists(filepath):
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    memory = get_memory()
    memory._sessions = data.get("sessions", {})