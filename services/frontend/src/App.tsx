import { useEffect } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { EditSellerPage, SellerAccountPage } from './pages/AccountPages'
import { LoginPage, RegisterPage } from './pages/AuthPages'
import { useAuthStore } from './store/auth'

function HomePage() {
  const userId = useAuthStore((state) => state.userId)
  return <Navigate to={userId ? `/sellers/${userId}` : '/login'} replace />
}

function SessionWatcher() {
  const navigate = useNavigate()
  useEffect(() => {
    const onExpired = () => navigate('/login', { replace: true })
    window.addEventListener('seller-session-expired', onExpired)
    return () => window.removeEventListener('seller-session-expired', onExpired)
  }, [navigate])
  return null
}

function App() {
  return (
    <Layout>
      <SessionWatcher />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/sellers/:sellerId" element={<SellerAccountPage />} />
        <Route path="/account/edit" element={<EditSellerPage />} />
        <Route path="*" element={<div className="state-page"><h1>Страница не найдена</h1><p>Проверьте адрес или вернитесь на главную.</p></div>} />
      </Routes>
    </Layout>
  )
}

export default App
