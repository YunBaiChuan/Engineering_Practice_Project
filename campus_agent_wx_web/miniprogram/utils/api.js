const app = getApp()

const request = (url, method, data) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.API_BASE_URL}${url}`,
      method: method,
      data: data,
      timeout: 60000,
      header: {
        'Content-Type': 'application/json'
      },
      success: (res) => {
        console.log('请求成功:', url, res.statusCode)
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(res.data)
        }
      },
      fail: (err) => {
        console.error('请求失败:', url, err)
        reject(err)
      }
    })
  })
}

// 登录
const login = (username, password) => {
  return request('/api/login', 'POST', { username, password })
}

// 注册
const register = (username, password, name) => {
  return request('/api/register', 'POST', { username, password, name })
}

// 聊天 - 调用流式接口
const chat = (message, userInfo) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.API_BASE_URL}/api/chat/stream`,
      method: 'POST',
      data: { message, user_info: userInfo },
      timeout: 60000,
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200) {
          // 流式响应返回的是 SSE 格式的文本
          const data = res.data
          if (typeof data === 'string') {
            // 解析 SSE 数据，提取完整的回复
            let fullContent = ''
            const lines = data.split('\n')
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const json = JSON.parse(line.slice(6))
                  if (json.content) fullContent += json.content
                  if (json.done) break
                } catch (e) {
                  console.error('解析 SSE 失败:', e)
                }
              }
            }
            resolve({ code: 200, data: { response: fullContent } })
          } else {
            resolve(data)
          }
        } else {
          reject(res)
        }
      },
      fail: reject
    })
  })
}

module.exports = {
  login,
  register,
  chat
}