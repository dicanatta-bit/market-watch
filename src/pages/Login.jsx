import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { login, user } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  if (user) {
    if (user.role === 'superadmin') navigate('/admin', { replace: true })
    else navigate(`/loc/${user.id_lokasi}`, { replace: true })
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); setError('')
    try {
      const data = await login(username, password)
      if (data.user?.role === 'superadmin') navigate('/admin', { replace: true })
      else navigate(`/loc/${data.user?.id_lokasi}`, { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Login gagal. Periksa username dan password.')
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-bold text-navy text-center mb-1">Market Watch AJN</h2>
        <p className="text-xs text-slate-500 text-center mb-5">Login untuk mengakses dashboard</p>
        {error && <div className="bg-red-50 text-red-700 text-xs p-2.5 rounded-lg mb-4 border border-red-200">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required autoFocus
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:border-gold focus:ring-1 focus:ring-gold outline-none"
              placeholder="superadmin@ajn.id atau knmp_xxx" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:border-gold focus:ring-1 focus:ring-gold outline-none" />
          </div>
          <button type="submit" className="w-full py-2.5 bg-navy text-white text-sm font-bold rounded-lg hover:bg-navy-dark transition">Login</button>
        </form>
        <p className="text-[11px] text-slate-400 text-center mt-4"><a href="/" className="text-navy hover:underline">← Kembali</a></p>
      </div>
    </div>
  )
}
