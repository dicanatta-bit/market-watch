import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/client.js'

const AuthContext = createContext(null)

function storeAuth(token, user) {
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
  api.defaults.headers.Authorization = `Bearer ${token}`
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const stored = localStorage.getItem('user')
    if (token && stored) {
      setUser(JSON.parse(stored))
      api.defaults.headers.Authorization = `Bearer ${token}`
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    try {
      const { data } = await api.post('/api/auth/login', { username, password })
      if (data.token) {
        storeAuth(data.token, data.user)
        setUser(data.user)
      }
      return data
    } catch {
      // ── Mock login — backend belum ready ──
      if (username === 'superadmin@ajn.id') {
        const mockUser = { id: 1, username, role: 'superadmin', id_lokasi: null, nama: 'Superadmin AJN' }
        storeAuth('mock-token-sa', mockUser)
        setUser(mockUser)
        return { token: 'mock-token-sa', user: mockUser }
      }
      const match = username.match(/^knmp_(\d+)$/)
      if (match) {
        const id_lokasi = parseInt(match[1])
        const mockUser = { id: 100 + id_lokasi, username, role: 'admin_lokasi', id_lokasi, nama: `Admin KNMP #${id_lokasi}` }
        storeAuth(`mock-token-${id_lokasi}`, mockUser)
        setUser(mockUser)
        return { token: `mock-token-${id_lokasi}`, user: mockUser }
      }
      throw new Error('Username tidak dikenal. Gunakan superadmin@ajn.id atau knmp_{id}')
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete api.defaults.headers.Authorization
    setUser(null)
  }

  const changePassword = async (oldPw, newPw) => {
    try {
      const { data } = await api.post('/api/auth/change-password', { old_password: oldPw, new_password: newPw })
      return data
    } catch {
      return { success: true, message: 'Password berhasil diubah (mock).' }
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, changePassword }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() { return useContext(AuthContext) }
