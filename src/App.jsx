import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import PublicLayout from './components/layout/PublicLayout.jsx'
import AdminLayout from './components/layout/AdminLayout.jsx'
import Home from './pages/Home.jsx'
import MapPage from './pages/MapPage.jsx'
import Login from './pages/Login.jsx'
import ChangePw from './pages/ChangePw.jsx'
import AdminDashboard from './pages/admin/AdminDashboard.jsx'
import Locations from './pages/admin/Locations.jsx'
import LocationDetail from './pages/admin/LocationDetail.jsx'
import Users from './pages/admin/Users.jsx'
import LocDashboard from './pages/location/LocDashboard.jsx'

function Protected({ children, role }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) {
    if (user.role === 'superadmin') return <Navigate to="/admin" replace />
    if (user.role === 'admin_lokasi') return <Navigate to={`/loc/${user.id_lokasi}`} replace />
    return <Navigate to="/" replace />
  }
  return children
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/peta" element={<MapPage />} />
        <Route path="/login" element={<Login />} />
      </Route>

      <Route path="/change-password" element={<ChangePw />} />

      <Route element={<Protected><AdminLayout /></Protected>}>
        <Route path="/admin" element={<Protected role="superadmin"><AdminDashboard /></Protected>} />
        <Route path="/admin/locations" element={<Protected role="superadmin"><Locations /></Protected>} />
        <Route path="/admin/locations/:id" element={<Protected role="superadmin"><LocationDetail /></Protected>} />
        <Route path="/admin/users" element={<Protected role="superadmin"><Users /></Protected>} />
      </Route>

      <Route element={<Protected><AdminLayout /></Protected>}>
        <Route path="/loc/:id" element={<LocDashboard />} />
      </Route>
    </Routes>
  )
}
