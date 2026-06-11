import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Input } from '../components/ui/Input.jsx'
import { Card, CardContent, CardTitle, CardHeader } from '../components/ui/Card.jsx'

export default function Login() {
  const { login, user, logout } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const data = await login(username, password)
      if (data.user?.role === 'superadmin') navigate('/admin', { replace: true })
      else navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Login gagal.')
    } finally { setLoading(false) }
  }

  if (user) {
    return (
      <div className="max-w-sm mx-auto mt-8">
        <Card>
          <CardHeader><CardTitle className="text-center">Anda Sudah Login</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground text-center">
              Login sebagai <strong>{user.nama || user.username}</strong> ({user.role})
            </p>
            <div className="flex gap-2">
              {user.role === 'superadmin' ? (
                <Link to="/admin" className="flex-1"><Button variant="gold" className="w-full">Dashboard Admin</Button></Link>
              ) : (
                <Link to="/" className="flex-1"><Button variant="gold" className="w-full">Halaman Utama</Button></Link>
              )}
              <Button variant="outline" className="flex-1" onClick={() => { logout(); setUsername(''); setPassword('') }}>Logout</Button>
            </div>
            <p className="text-xs text-muted-foreground text-center"><Link to="/" className="hover:underline">← Kembali ke Website</Link></p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-sm mx-auto mt-8">
      <Card>
        <CardHeader><CardTitle className="text-center">Login Market Watch</CardTitle></CardHeader>
        <CardContent>
          {error && <div className="bg-destructive/10 text-destructive text-xs p-3 rounded-lg mb-4 border border-destructive/20">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-3">
            <Input type="text" placeholder="superadmin@ajn.id" value={username} onChange={e => setUsername(e.target.value)} required autoFocus />
            <Input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
            <Button type="submit" variant="gold" className="w-full" disabled={loading}>{loading ? 'Loading...' : 'Login'}</Button>
          </form>
          <p className="text-xs text-muted-foreground text-center mt-4"><Link to="/" className="hover:underline">← Kembali ke Website</Link></p>
        </CardContent>
      </Card>
    </div>
  )
}
