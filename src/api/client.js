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

// ── Mock data ──
import { mockKnmp, mockPrices, mockRegional, mockStats } from './mockData.js'

async function tryAPI(url, mockData, label) {
  try {
    const { data } = await api.get(url)
    // Vite returns HTML for unknown routes - check if valid data
    if (data && typeof data === 'object' && (data.data || data.success !== undefined)) {
      return data.data || data
    }
    throw new Error('Invalid API response')
  } catch {
    console.debug(`📦 ${label}: mock data`)
    return mockData
  }
}

export function fetchKnmp()          { return tryAPI('/api/knmp', mockKnmp, 'KNMP') }
export function fetchPrices()        { return tryAPI('/api/prices', mockPrices, 'Harga') }
export function fetchRegionalPrices(){ return tryAPI('/api/prices/regional', mockRegional, 'Wilayah') }
export function fetchStats()         { return tryAPI('/api/stats', mockStats, 'Stats') }
