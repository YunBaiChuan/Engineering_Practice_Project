const api = require('../../utils/api')

Page({
  data: {
    username: '',
    password: '',
    showPassword: false,
    rememberMe: false,
    loading: false,
    error: ''
  },

  onLoad() {
    // 自动填充记住的用户名
    const rememberedUser = wx.getStorageSync('rememberedUser')
    if (rememberedUser) {
      this.setData({ 
        username: rememberedUser,
        rememberMe: true
      })
    }
  },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value, error: '' })
  },
  
  onPasswordInput(e) {
    this.setData({ password: e.detail.value, error: '' })
  },
  
  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },
  
  toggleRemember() {
    this.setData({ rememberMe: !this.data.rememberMe })
  },

  handleLogin() {
    const { username, password, rememberMe } = this.data
    
    if (!username || !password) {
      this.setData({ error: '请填写完整' })
      return
    }

    this.setData({ loading: true, error: '' })

    api.login(username, password)
      .then(res => {
        if (res.code === 200) {
          // 保存用户信息
          wx.setStorageSync('user', {
            id: res.data.id,
            username: res.data.username,
            name: res.data.name,
            password: password
          })
          
          // 保存记住的用户名
          if (rememberMe) {
            wx.setStorageSync('rememberedUser', username)
          } else {
            wx.removeStorageSync('rememberedUser')
          }
          
          // 跳转到聊天页
          wx.reLaunch({ url: '/pages/chat/chat' })
        } else {
          this.setData({ error: res.detail || '登录失败' })
        }
      })
      .catch(err => {
        console.error('登录错误:', err)
        this.setData({ error: '网络错误，请检查后端服务是否启动' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  goToRegister() {
    wx.navigateTo({ url: '/pages/register/register' })
  }
})