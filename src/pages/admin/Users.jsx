import { useState } from 'react'
import api from '../../api/client.js'

const MOCK_USERS = [
  { id: 1, username: 'superadmin@ajn.id', role: 'superadmin', nama: 'Superadmin AJN', id_lokasi: null, is_active: true, last_login: '2026-06-09' },
  { id: 2, username: 'knmp_1363', role: 'admin_lokasi', nama: 'Kuala Tadu', id_lokasi: 1363, is_active: true, last_login: null },
  { id: 3, username: 'knmp_1', role: 'admin_lokasi', nama: 'Kuala Raja', id_lokasi: 1, is_active: true, last_login: '2026-06-09' },
  { id: 4, username: 'knmp_2', role: 'admin_lokasi', nama: 'Lancok', id_lokasi: 2, is_active: true, last_login: null },
]

export default function Users() {
  const [users] = useState(MOCK_USERS)
  const [msg, setMsg] = useState('')

  const resetPw = async (userId) => {
    try {
      await api.post(`/api/users/${userId}/reset-pw`)
      setMsg(`Password user #${userId} direset.`)
      setTimeout(() => setMsg(''), 3000)
    } catch { setMsg('Gagal mereset password.') }
  }

  return (
    <div>
      <h2 className="text-base font-bold text-navy mb-4">Manage Users</h2>
      {msg && <div className="bg-emerald-50 text-emerald-700 text-xs p-2.5 rounded-lg mb-4 border border-emerald-200">{msg}</div>}
      <div className="bg-white rounded-xl shadow-sm overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wide">
            <th className="p-2.5 text-left">ID</th><th className="p-2.5 text-left">Username</th><th className="p-2.5 text-left">Role</th><th className="p-2.5 text-left">Nama</th><th className="p-2.5 text-left">Lokasi</th><th className="p-2.5 text-left">Status</th><th className="p-2.5 text-left">Last Login</th><th></th>
          </tr></thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="p-2.5">{u.id}</td><td className="p-2.5 font-semibold">{u.username}</td>
                <td className="p-2.5"><span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${u.role === 'superadmin' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'}`}>{u.role}</span></td>
                <td className="p-2.5">{u.nama}</td><td className="p-2.5">{u.id_lokasi || '—'}</td>
                <td className="p-2.5"><span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${u.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                <td className="p-2.5">{u.last_login || '—'}</td>
                <td className="p-2.5"><button onClick={() => resetPw(u.id)} className="px-3 py-1 text-[10px] font-semibold bg-white border border-navy text-navy rounded-lg hover:bg-slate-50">Reset PW</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
