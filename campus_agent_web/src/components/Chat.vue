<template>
  <div class="chat-container">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'sidebar-hidden': !showSidebar }">
      <div class="sidebar-header">
        <h2>历史对话</h2>
        <button @click="toggleSidebar" class="close-sidebar lg:hidden">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
      
      <button @click="startNewChat" class="new-chat-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        新对话
      </button>

      <div class="history-list">
        <div v-if="chatHistory.length === 0" class="empty-history">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <p>暂无历史对话</p>
        </div>

        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          @click="loadChatHistory(chat.id)"
          class="history-item"
          :class="{ active: activeChatId === chat.id }"
        >
          <div class="history-content">
            <p class="history-title">{{ chat.title }}</p>
            <p class="history-preview">{{ chat.lastMessage }}</p>
            <span class="history-time">{{ chat.time }}</span>
          </div>
          <button @click.stop="showDeleteConfirm(chat.id)" class="delete-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <header class="chat-header">
        <button @click="toggleSidebar" class="menu-btn lg:hidden">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 6h16M4 12h16M4 18h7"/>
          </svg>
        </button>
        
        <div class="header-info">
          <div class="avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
          </div>
          <div>
            <h1>智能体助手</h1>
            <span class="status" :class="{ online: isConnected, offline: !isConnected }">
              {{ isConnected ? '在线' : '离线' }}
            </span>
          </div>
        </div>
        
        <button @click="showLogoutConfirm" class="logout-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
          </svg>
          <span>退出登录</span>
        </button>
      </header>

      <div ref="messagesContainer" class="messages-area">
        <div class="messages-wrapper">
          <div class="welcome-banner">
            <div class="welcome-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 8v4l3 3M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
              </svg>
            </div>
            <p>我是您的智能助手，可以帮您查询课表、成绩等信息</p>
          </div>

          <div 
            v-for="(message, index) in messages" 
            :key="index"
            class="message"
            :class="message.isUser ? 'user-message' : 'bot-message'"
          >
            <div class="message-avatar">
              <svg v-if="!message.isUser" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <div class="message-bubble">
              <div v-if="!message.isUser" class="markdown-content" v-html="message.renderedHtml || message.content"></div>
              <p v-else class="message-text">{{ message.content }}</p>
              <span class="message-time">{{ message.time }}</span>
            </div>
          </div>

          <div v-if="isStreaming" class="message bot-message">
            <div class="message-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
            </div>
            <div class="message-bubble typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <footer class="chat-footer">
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            @keydown.enter.exact.prevent="sendMessage"
            placeholder="输入消息... (例如：今天有什么课？)"
            rows="1"
            class="message-input"
          ></textarea>
          <button 
            @click="sendMessage" 
            :disabled="!inputMessage.trim() || isStreaming"
            class="send-btn"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
        <p class="input-hint">Enter 发送，Shift+Enter 换行</p>
      </footer>
    </main>

    <!-- 自定义确认弹窗 -->
    <div v-if="showConfirm" class="confirm-overlay" @click.self="closeConfirm">
      <div class="confirm-modal">
        <div class="confirm-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>
        <h3>{{ confirmTitle }}</h3>
        <p>{{ confirmMessage }}</p>
        <div class="confirm-buttons">
          <button class="confirm-btn cancel" @click="closeConfirm">取消</button>
          <button class="confirm-btn ok" @click="confirmAction">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true, headerIds: false, mangle: false })

const renderer = new marked.Renderer()
renderer.link = (href, title, text) => {
  return `<a href="${href}" target="_blank" rel="noopener noreferrer" title="${title || ''}">${text}</a>`
}
marked.use({ renderer })

const router = useRouter()
const API_BASE_URL = 'http://localhost:5000'

const messages = ref([])
const inputMessage = ref('')
const isStreaming = ref(false)
const isConnected = ref(true)
const messagesContainer = ref(null)
const showSidebar = ref(false)
const activeChatId = ref(null)
const chatHistory = ref([])
const currentUser = ref(null)

// 确认弹窗相关
const showConfirm = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
let confirmCallback = null

const showLogoutConfirm = () => {
  confirmTitle.value = '确认退出'
  confirmMessage.value = '确定要退出登录吗？'
  confirmCallback = () => {
    handleLogout()
  }
  showConfirm.value = true
}

const showDeleteConfirm = (chatId) => {
  confirmTitle.value = '删除对话'
  confirmMessage.value = '确定要删除这个对话吗？'
  confirmCallback = () => {
    deleteChat(chatId)
  }
  showConfirm.value = true
}

const closeConfirm = () => {
  showConfirm.value = false
  confirmCallback = null
}

const confirmAction = () => {
  if (confirmCallback) {
    confirmCallback()
  }
  closeConfirm()
}

const getTime = () => {
  const now = new Date()
  return now.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const getFullTime = () => {
  const now = new Date()
  return now.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    return marked.parse(content)
  } catch (e) {
    return content.replace(/\n/g, '<br>')
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const getUserInfo = () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return { username: user.username || '', password: user.password || '' }
}

const sendMessageStream = async (message) => {
  try {
    const userInfo = getUserInfo()
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message, 
        history: messages.value.filter(m => !m.isUser).slice(-10),
        user_info: userInfo
      })
    })
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''
    const tempMessageIndex = messages.value.length
    messages.value.push({ content: '', renderedHtml: '', isUser: false, time: getTime(), isStreaming: true })
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.slice(6)
            if (jsonStr.trim() === '[DONE]') {
              messages.value[tempMessageIndex].isStreaming = false
              continue
            }
            const data = JSON.parse(jsonStr)
            if (data.content) {
              fullContent += data.content
              messages.value[tempMessageIndex].content = fullContent
              messages.value[tempMessageIndex].renderedHtml = renderMarkdown(fullContent)
              await scrollToBottom()
            }
            if (data.done) messages.value[tempMessageIndex].isStreaming = false
            if (data.error) {
              messages.value[tempMessageIndex].content = `错误: ${data.error}`
              messages.value[tempMessageIndex].renderedHtml = `<p class="error">错误: ${data.error}</p>`
              messages.value[tempMessageIndex].isStreaming = false
            }
          } catch (e) {}
        }
      }
    }
    if (fullContent) saveChatHistory()
    return fullContent
  } catch (error) {
    isConnected.value = false
    throw error
  }
}

const sendMessageNormal = async (message) => {
  try {
    const userInfo = getUserInfo()
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history: messages.value.filter(m => !m.isUser).slice(-10), user_info: userInfo })
    })
    const data = await response.json()
    return data.code === 200 ? data.data.response : `抱歉，出了点问题：${data.error || '未知错误'}`
  } catch (error) {
    isConnected.value = false
    return `网络连接失败，请检查后端服务是否启动。`
  }
}

const saveChatHistory = () => {
  if (messages.value.length <= 1 || !currentUser.value) return
  const chatId = activeChatId.value
  if (!chatId) return
  
  const messagesToSave = messages.value.map(m => ({ content: m.content, isUser: m.isUser, time: m.time }))
  const chatData = {
    id: chatId, userId: currentUser.value.id,
    title: messages.value[1]?.content?.substring(0, 30) + '...' || '新对话',
    lastMessage: messages.value[messages.value.length - 1]?.content?.substring(0, 50) + '...' || '',
    time: getFullTime(), messages: messagesToSave
  }
  let history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  const existingIndex = history.findIndex(c => c.id === chatData.id)
  existingIndex >= 0 ? history[existingIndex] = chatData : history.unshift(chatData)
  if (history.length > 50) history = history.slice(0, 50)
  localStorage.setItem('chatHistory', JSON.stringify(history))
  loadChatHistoryList()
}

const loadChatHistoryList = () => {
  if (!currentUser.value) return
  const history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  chatHistory.value = history.filter(c => c.userId === currentUser.value.id)
}

const loadChatHistory = (chatId) => {
  const history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  const chat = history.find(c => c.id === chatId)
  if (chat) {
    messages.value = chat.messages.map(m => ({ ...m, renderedHtml: !m.isUser ? renderMarkdown(m.content) : null }))
    activeChatId.value = chatId
    showSidebar.value = false
    scrollToBottom()
  }
}

const deleteChat = (chatId) => {
  let history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  history = history.filter(c => c.id !== chatId)
  localStorage.setItem('chatHistory', JSON.stringify(history))
  loadChatHistoryList()
  if (activeChatId.value === chatId) startNewChat()
}

const startNewChat = () => {
  if (!currentUser.value) { router.push('/'); return }
  const greetingContent = `你好，同学！👋\n\n我是你的校园智能助手，可以帮你：\n\n📚 **查课表** — 问"今天有什么课"、"明天有课吗"\n📊 **查成绩** — 问"我的成绩怎么样"\n⏰ **查时间** — 问"现在第几周"\n\n试试问我吧！有什么需要帮忙的吗？`
  messages.value = [{ content: greetingContent, isUser: false, time: getTime(), renderedHtml: renderMarkdown(greetingContent) }]
  activeChatId.value = Date.now().toString()
  showSidebar.value = false
  scrollToBottom()
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isStreaming.value) return
  messages.value.push({ content: inputMessage.value.trim(), isUser: true, time: getTime() })
  const userInput = inputMessage.value.trim()
  inputMessage.value = ''
  await scrollToBottom()
  isStreaming.value = true
  isConnected.value = true
  
  try {
    let success = false
    try {
      const testResponse = await fetch(`${API_BASE_URL}/api/health`)
      if (testResponse.ok) { await sendMessageStream(userInput); success = true }
    } catch (e) {}
    if (!success) {
      const botResponseText = await sendMessageNormal(userInput)
      messages.value.push({ content: botResponseText, isUser: false, time: getTime(), renderedHtml: renderMarkdown(botResponseText) })
      await scrollToBottom()
      saveChatHistory()
    }
  } catch (error) {
    messages.value.push({ content: '抱歉，服务暂时不可用。请稍后重试。', isUser: false, time: getTime(), renderedHtml: '<p class="error">抱歉，服务暂时不可用。请稍后重试。</p>' })
    await scrollToBottom()
  } finally {
    isStreaming.value = false
  }
}

const clearInput = () => { inputMessage.value = '' }
const toggleSidebar = () => { showSidebar.value = !showSidebar.value }

const handleLogout = () => {
  localStorage.removeItem('user')
  router.push('/')
}

const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`)
    const data = await response.json()
    isConnected.value = data.code === 200
  } catch (error) { isConnected.value = false }
}

let healthInterval = null
onMounted(() => {
  const user = JSON.parse(localStorage.getItem('user'))
  if (!user) { router.push('/'); return }
  currentUser.value = user
  checkHealth()
  healthInterval = setInterval(checkHealth, 30000)
  loadChatHistoryList()
  const history = JSON.parse(localStorage.getItem('chatHistory') || '[]')
  const defaultChat = history.find(c => c.userId === user.id && c.id === 'default')
  if (defaultChat && defaultChat.messages?.length > 0) {
    messages.value = defaultChat.messages.map(m => ({ ...m, renderedHtml: !m.isUser ? renderMarkdown(m.content) : null }))
    activeChatId.value = 'default'
  } else { startNewChat(); activeChatId.value = 'default' }
  scrollToBottom()
})
onUnmounted(() => { if (healthInterval) clearInterval(healthInterval) })
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.chat-container {
  display: flex;
  height: 100vh;
  width: 100%;
  background: #f0f2f5;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  background: white;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 20;
  border-right: 1px solid #e5e7eb;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.close-sidebar {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #9ca3af;
}

.close-sidebar svg {
  width: 20px;
  height: 20px;
}

.new-chat-btn {
  margin: 16px;
  padding: 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.new-chat-btn svg {
  width: 18px;
  height: 18px;
  stroke: white;
}

.new-chat-btn:hover {
  background: #2563eb;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.empty-history {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.empty-history svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.history-item {
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.history-item:hover {
  background: #f3f4f6;
}

.history-item.active {
  background: #eff6ff;
}

.history-content {
  flex: 1;
  min-width: 0;
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-preview {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.history-time {
  font-size: 10px;
  color: #9ca3af;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  color: #9ca3af;
  transition: all 0.2s;
  flex-shrink: 0;
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

.delete-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
}

.chat-header {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.menu-btn {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  color: #6b7280;
}

.menu-btn svg {
  width: 24px;
  height: 24px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  background: #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar svg {
  width: 22px;
  height: 22px;
  stroke: white;
}

.header-info h1 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 20px;
  background: #f3f4f6;
  color: #6b7280;
}

.status.online {
  background: #d1fae5;
  color: #059669;
}

.status.offline {
  background: #fee2e2;
  color: #dc2626;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: #ef4444;
  border: none;
  cursor: pointer;
  color: white;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.logout-btn svg {
  width: 18px;
  height: 18px;
  stroke: white;
}

.logout-btn:hover {
  background: #dc2626;
}

/* 消息区域 */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #fafbfc;
}

.messages-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.welcome-banner {
  text-align: center;
  margin-bottom: 32px;
  padding: 24px;
  background: #f3f4f6;
  border-radius: 24px;
}

.welcome-icon {
  width: 56px;
  height: 56px;
  background: #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}

.welcome-icon svg {
  width: 28px;
  height: 28px;
  stroke: white;
}

.welcome-banner p {
  color: #6b7280;
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  animation: fadeInUp 0.3s ease-out;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  background: #e5e7eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-message .message-avatar {
  background: #3b82f6;
}

.message-avatar svg {
  width: 20px;
  height: 20px;
  stroke: #6b7280;
}

.user-message .message-avatar svg {
  stroke: white;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 20px;
  background: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.user-message .message-bubble {
  background: #3b82f6;
  color: white;
  border: none;
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.message-time {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 6px;
  display: block;
  text-align: right;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.6);
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 14px 20px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: scale(1); opacity: 0.4; }
  30% { transform: scale(1.2); opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Markdown 内容 */
.markdown-content :deep(p) { margin: 0 0 8px; }
.markdown-content :deep(p:last-child) { margin-bottom: 0; }
.markdown-content :deep(code) { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
.markdown-content :deep(pre) { background: #f3f4f6; padding: 12px; border-radius: 8px; overflow-x: auto; }
.markdown-content :deep(ul), .markdown-content :deep(ol) { margin: 8px 0; padding-left: 20px; }
.markdown-content :deep(li) { margin: 4px 0; }
.markdown-content :deep(a) { color: #3b82f6; text-decoration: none; }
.user-message .markdown-content :deep(code) { background: rgba(255,255,255,0.2); color: white; }
.user-message .markdown-content :deep(pre) { background: rgba(255,255,255,0.1); }

/* 输入区域 */
.chat-footer {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  font-size: 14px;
  resize: none;
  outline: none;
  transition: all 0.2s;
  font-family: inherit;
  max-height: 120px;
  background: #fafbfc;
}

.message-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: white;
}

.send-btn {
  width: 44px;
  height: 44px;
  background: #3b82f6;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn svg {
  width: 20px;
  height: 20px;
  stroke: white;
}

.send-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hint {
  text-align: center;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 10px;
}

/* 自定义确认弹窗 */
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-modal {
  background: white;
  border-radius: 20px;
  padding: 28px 32px;
  width: 320px;
  text-align: center;
  animation: scaleIn 0.2s ease-out;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.confirm-icon {
  width: 56px;
  height: 56px;
  background: #fee2e2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.confirm-icon svg {
  width: 28px;
  height: 28px;
  stroke: #ef4444;
}

.confirm-modal h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.confirm-modal p {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 24px;
}

.confirm-buttons {
  display: flex;
  gap: 12px;
}

.confirm-btn {
  flex: 1;
  padding: 10px 0;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.confirm-btn.cancel {
  background: #f3f4f6;
  color: #6b7280;
}

.confirm-btn.cancel:hover {
  background: #e5e7eb;
}

.confirm-btn.ok {
  background: #ef4444;
  color: white;
}

.confirm-btn.ok:hover {
  background: #dc2626;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    transform: translateX(0);
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  }
  
  .sidebar-hidden {
    transform: translateX(-100%);
  }
  
  .menu-btn {
    display: block;
  }
  
  .message-bubble {
    max-width: 85%;
  }
  
  .confirm-modal {
    width: 280px;
    padding: 24px;
  }
}
</style>