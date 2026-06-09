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
      {/* Public pages with shared header */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
      </Route>

      {/* Fullscreen map — no layout wrapper */}
      <Route path="/peta" element={<MapPage />} />

      {/* Change password — standalone */}
      <Route path="/change-password" element={<ChangePw />} />

      {/* Superadmin routes */}
      <Route element={<Protected role="superadmin"><AdminLayout /></Protected>}>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/locations" element={<Locations />} />
        <Route path="/admin/locations/:id" element={<LocationDetail />} />
        <Route path="/admin/users" element={<Users />} />
      </Route>

      {/* Location admin routes */}
      <Route element={<Protected><AdminLayout /></Protected>}>
        <Route path="/loc/:id" element={<LocDashboard />} />
      </Route>
    </Routes>
  )
}
