import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import PublicLayout from './components/layout/PublicLayout.jsx'
import Home from './pages/Home.jsx'
import MapPage from './pages/MapPage.jsx'
import Login from './pages/Login.jsx'
import Admin from './pages/Admin.jsx'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'superadmin') return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
      </Route>
      <Route path="/peta" element={<MapPage />} />
      <Route path="/admin" element={<Protected><Admin /></Protected>} />
    </Routes>
  )
}
