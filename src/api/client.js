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

// Real API — fallback to mock only if backend is down
async function fetchOrMock(url, mockData, label) {
  try {
    const { data } = await api.get(`/api${url}`)
    if (data && data.data) return data.data
    if (data && Array.isArray(data)) return data
    return mockData
  } catch (e) {
    console.debug(`📦 ${label}: mock`)
    return mockData
  }
}

import { mockKnmp, mockPrices, mockRegional, mockStats } from './mockData.js'

export function fetchKnmp()          { return fetchOrMock('/knmp', mockKnmp, 'KNMP') }
export function fetchPrices()        { return fetchOrMock('/prices', mockPrices, 'Harga') }
export function fetchRegionalPrices(){ return fetchOrMock('/prices/regional', mockRegional, 'Wilayah') }
export function fetchStats()         { return fetchOrMock('/stats', mockStats, 'Stats') }
