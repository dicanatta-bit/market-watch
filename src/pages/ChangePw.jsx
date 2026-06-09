import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function ChangePw() {
  const { changePassword } = useAuth()
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirm, setConfirm] = useState('')
  const [msg, setMsg] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault(); setMsg('')
    if (newPw !== confirm) return setMsg('Password baru tidak cocok.')
    if (newPw.length < 6) return setMsg('Minimal 6 karakter.')
    try {
      await changePassword(oldPw, newPw)
      setMsg('Password berhasil diubah!')
      setTimeout(() => navigate(-1), 1500)
    } catch {
      setMsg('Gagal. Periksa password lama.')
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-bold text-navy text-center mb-4">Ganti Password</h2>
        {msg && <div className={`text-xs p-2.5 rounded-lg mb-4 border ${msg.includes('berhasil') ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'}`}>{msg}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div><label className="block text-xs font-semibold text-slate-600 mb-1">Password Lama</label><input type="password" value={oldPw} onChange={e => setOldPw(e.target.value)} required className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:border-gold outline-none" /></div>
          <div><label className="block text-xs font-semibold text-slate-600 mb-1">Password Baru</label><input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} required minLength={6} className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:border-gold outline-none" /></div>
          <div><label className="block text-xs font-semibold text-slate-600 mb-1">Konfirmasi</label><input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:border-gold outline-none" /></div>
          <button type="submit" className="w-full py-2.5 bg-gold text-white text-sm font-bold rounded-lg hover:bg-amber-600 transition">Simpan</button>
        </form>
      </div>
    </div>
  )
}
