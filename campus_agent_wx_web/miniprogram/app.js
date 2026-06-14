App({
  globalData: {
    API_BASE_URL: 'https://zoning-mouth-stapling.ngrok-free.dev'
  },
  onLaunch() {
    console.log('API_BASE_URL:', this.globalData.API_BASE_URL)
  }
})