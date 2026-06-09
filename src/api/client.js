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

// ── Mock fallback for development (remove when backend is ready) ──
import { mockKnmp, mockPrices, mockRegional, mockStats } from './mockData.js'

export async function fetchKnmp() {
  try {
    const { data } = await api.get('/api/knmp')
    return data.data
  } catch {
    console.warn('BE unavailable, using mock knmp data')
    return mockKnmp
  }
}

export async function fetchPrices() {
  try {
    const { data } = await api.get('/api/prices')
    return data.data
  } catch {
    return mockPrices
  }
}

export async function fetchRegionalPrices() {
  try {
    const { data } = await api.get('/api/prices/regional')
    return data.data
  } catch {
    return mockRegional
  }
}

export async function fetchStats() {
  try {
    const { data } = await api.get('/api/stats')
    return data.data
  } catch {
    return mockStats
  }
}
