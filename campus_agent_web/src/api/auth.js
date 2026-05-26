// src/api/auth.js
const API_BASE_URL = 'http://localhost:5000'

export const authAPI = {
  // 登录
  async login(username, password) {
    const response = await fetch(`${API_BASE_URL}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    })
    
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || data.message || '登录失败')
    }
    return data
  },
  
  // 注册
  async register(username, password, name = '') {
    const response = await fetch(`${API_BASE_URL}/api/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password, name })
    })
    
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || data.message || '注册失败')
    }
    return data
  },
  
  // 登出
  async logout() {
    const response = await fetch(`${API_BASE_URL}/api/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    return response.json()
  }
}