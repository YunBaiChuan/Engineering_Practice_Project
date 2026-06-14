const api = require('../../utils/api')

Page({
  data: {
    messages: [],
    inputMessage: '',
    isTyping: false,
    isConnected: true,
    user: null,
    scrollIntoView: ''
  },

  onLoad() {
    const user = wx.getStorageSync('user')
    if (!user) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.setData({ user })
    this.addWelcomeMessage(user)
    // 健康检查已移除，默认在线
  },

  addWelcomeMessage(user) {
    const userName = user.name || user.username || '同学'
    const greeting = `你好，同学！👋\n\n我是你的校园智能助手，可以帮你：\n\n📚 **查课表** — “今天有什么课”\n📊 **查成绩** — “我的成绩怎么样”\n📅 **查考试** — “考试安排”\n⏰ **查时间** — “现在第几周”\n\n试试问我吧！有什么需要帮忙的吗？`
    
    this.setData({
      messages: [{
        isUser: false,
        content: greeting,
        richText: this.formatMarkdown(greeting),
        time: this.getTime()
      }]
    })
    this.scrollToBottom()
  },

  formatMarkdown(text) {
    if (!text) return ''
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>')
  },

  onInput(e) {
    this.setData({ inputMessage: e.detail.value })
  },

  sendMessage() {
    const { inputMessage, messages, user } = this.data
    if (!inputMessage.trim()) return

    const userMessage = {
      isUser: true,
      content: inputMessage,
      time: this.getTime()
    }
    messages.push(userMessage)
    this.setData({ messages, inputMessage: '', isTyping: true })
    this.scrollToBottom()

    api.chat(inputMessage, { username: user.username, password: user.password })
      .then(res => {
        if (res.code === 200) {
          const content = res.data.response
          const botMessage = {
            isUser: false,
            content: content,
            richText: this.formatMarkdown(content),
            time: this.getTime()
          }
          messages.push(botMessage)
          this.setData({ messages, isTyping: false })
          this.scrollToBottom()
        } else {
          wx.showToast({ title: '请求失败', icon: 'none' })
          this.setData({ isTyping: false })
        }
      })
      .catch(err => {
        console.error(err)
        wx.showToast({ title: '网络错误', icon: 'none' })
        this.setData({ isTyping: false })
      })
  },

  getTime() {
    const now = new Date()
    const month = now.getMonth() + 1
    const date = now.getDate()
    const hours = now.getHours().toString().padStart(2, '0')
    const minutes = now.getMinutes().toString().padStart(2, '0')
    return `${month}/${date} ${hours}:${minutes}`
  },

  // 滚动到底部
  scrollToBottom() {
    const messages = this.data.messages
    if (messages.length === 0) return
    
    // 滚动到最后一条消息
    const lastIndex = messages.length - 1
    this.setData({
      scrollIntoView: `msg-${lastIndex}`
    })
  },

  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('user')
          wx.reLaunch({ url: '/pages/login/login' })
        }
      }
    })
  }
})