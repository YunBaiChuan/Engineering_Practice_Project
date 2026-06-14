const api = require('../../utils/api')

Page({
  data: {
    username: '',
    password: '',
    confirmPassword: '',
    name: '',
    agree: false,
    showPassword: false,
    showConfirm: false,
    loading: false,
    error: ''
  },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value, error: '' })
  },
  
  onPasswordInput(e) {
    this.setData({ password: e.detail.value, error: '' })
  },
  
  onConfirmInput(e) {
    this.setData({ confirmPassword: e.detail.value, error: '' })
  },
  
  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },
  
  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },
  
  toggleConfirm() {
    this.setData({ showConfirm: !this.data.showConfirm })
  },
  
  toggleAgree() {
    this.setData({ agree: !this.data.agree })
  },

  handleRegister() {
    const { username, password, confirmPassword, name, agree } = this.data
    
    // 前端验证
    if (!username.trim()) {
      this.setData({ error: '请输入学号' })
      return
    }
    
    if (password !== confirmPassword) {
      this.setData({ error: '两次输入的密码不一致' })
      return
    }
    
    if (password.length < 6) {
      this.setData({ error: '密码长度至少为6位' })
      return
    }
    
    if (!agree) {
      this.setData({ error: '请同意服务条款和隐私政策' })
      return
    }
    
    this.setData({ loading: true, error: '' })

    // 调用后端注册API
    api.register(username, password, name || username)
      .then(res => {
        if (res.code === 200) {
          wx.showModal({
            title: '注册成功',
            content: '请登录',
            showCancel: false,
            success: () => {
              wx.navigateBack()
            }
          })
        } else {
          this.setData({ error: res.detail || res.message || '注册失败' })
        }
      })
      .catch(err => {
        console.error('注册错误:', err)
        this.setData({ error: '网络错误，请检查后端服务是否启动' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  goToLogin() {
    wx.navigateBack()
  }
})