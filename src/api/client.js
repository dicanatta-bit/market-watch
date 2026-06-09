import axios from 'axios'

const api = axios.create({ baseURL: '' })

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// Mock data imports
import { mockKnmp, mockPrices, mockRegional, mockStats } from './mockData.js'

// Helper: try API, fallback to mock
async function tryAPI(getter, mockData, label) {
  try {
    const { data } = await api.get(getter)
    return data.data || data
  } catch {
    console.info(`📦 ${label}: menggunakan mock data (BE belum tersedia)`)
    return mockData
  }
}

export async function fetchKnmp() {
  return tryAPI('/api/knmp', mockKnmp, 'KNMP')
}

export async function fetchPrices() {
  return tryAPI('/api/prices', mockPrices, 'Harga')
}

export async function fetchRegionalPrices() {
  return tryAPI('/api/prices/regional', mockRegional, 'Harga Wilayah')
}

export async function fetchStats() {
  return tryAPI('/api/stats', mockStats, 'Statistik')
}
