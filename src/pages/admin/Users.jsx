import { useState } from 'react'
import api from '../../api/client.js'
import { Card } from '../../components/ui/Card.jsx'
import { Button } from '../../components/ui/Button.jsx'
import { Badge } from '../../components/ui/Badge.jsx'
import { Table, TableBody, TableRow, TableCell, TableHead, TableHeader } from '../../components/ui/Table.jsx'
import { Skeleton } from '../../components/ui/Skeleton.jsx'

const MOCK_USERS = [
  { id: 1, username: 'superadmin@ajn.id', role: 'superadmin', nama: 'Superadmin AJN', id_lokasi: null, is_active: true, last_login: '2026-06-09' },
  { id: 2, username: 'knmp_1', role: 'admin_lokasi', nama: 'Kuala Raja', id_lokasi: 1, is_active: true, last_login: '2026-06-09' },
  { id: 3, username: 'knmp_1363', role: 'admin_lokasi', nama: 'Kuala Tadu', id_lokasi: 1363, is_active: true, last_login: null },
]

export default function Users() {
  const [users] = useState(MOCK_USERS)
  const [msg, setMsg] = useState('')

  const resetPw = async (id) => {
    try { await api.post(`/api/users/${id}/reset-pw`); setMsg(`Password user #${id} direset.`) } catch { setMsg('Gagal.') }
    setTimeout(()=>setMsg(''),3000)
  }

  return (
    <div>
      <h2 className="text-base font-bold text-foreground mb-4">Manage Users</h2>
      {msg && <div className="bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 text-xs p-3 rounded-lg mb-4 border border-emerald-200 dark:border-emerald-800">{msg}</div>}
      <Card className="overflow-hidden">
        <Table>
          <TableHeader><TableRow><TableHead>ID</TableHead><TableHead>Username</TableHead><TableHead>Role</TableHead><TableHead>Nama</TableHead><TableHead>Lokasi</TableHead><TableHead>Status</TableHead><TableHead>Login</TableHead><TableHead></TableHead></TableRow></TableHeader>
          <TableBody>
            {users.map(u=>(
              <TableRow key={u.id}>
                <TableCell className="text-xs">{u.id}</TableCell><TableCell className="text-xs font-semibold">{u.username}</TableCell>
                <TableCell><Badge variant={u.role==='superadmin'?'success':'info'} className="text-[10px]">{u.role}</Badge></TableCell>
                <TableCell className="text-xs">{u.nama}</TableCell><TableCell className="text-xs">{u.id_lokasi||'—'}</TableCell>
                <TableCell><Badge variant={u.is_active?'success':'destructive'} className="text-[10px]">{u.is_active?'Active':'Inactive'}</Badge></TableCell>
                <TableCell className="text-xs text-muted-foreground">{u.last_login||'—'}</TableCell>
                <TableCell><Button variant="outline" size="xs" onClick={()=>resetPw(u.id)}>Reset PW</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
