import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Input } from '../components/ui/Input.jsx'
import { Card, CardContent, CardTitle, CardHeader } from '../components/ui/Card.jsx'

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
    try { await changePassword(oldPw, newPw); setMsg('Berhasil!'); setTimeout(()=>navigate(-1),1500) }
    catch { setMsg('Gagal. Periksa password lama.') }
  }

  return (
    <div className="max-w-sm mx-auto mt-8">
      <Card>
        <CardHeader><CardTitle className="text-center">Ganti Password</CardTitle></CardHeader>
        <CardContent>
          {msg && <div className={`text-xs p-3 rounded-lg mb-4 border ${msg.includes('Berhasil')?'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 border-emerald-200':'bg-destructive/10 text-destructive border-destructive/20'}`}>{msg}</div>}
          <form onSubmit={handleSubmit} className="space-y-3">
            <Input type="password" placeholder="Password Lama" value={oldPw} onChange={e=>setOldPw(e.target.value)} required />
            <Input type="password" placeholder="Password Baru" value={newPw} onChange={e=>setNewPw(e.target.value)} required minLength={6} />
            <Input type="password" placeholder="Konfirmasi" value={confirm} onChange={e=>setConfirm(e.target.value)} required />
            <Button type="submit" variant="gold" className="w-full">Simpan</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
