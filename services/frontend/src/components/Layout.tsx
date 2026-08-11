import type { PropsWithChildren } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

export function Layout({ children }: PropsWithChildren) {
  const { userId, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const logout = () => {
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to={userId ? `/sellers/${userId}` : '/'}>MARKETPLACE</Link>
        <nav aria-label="Основная навигация">
          {userId ? (
            <>
              <Link to={`/sellers/${userId}`}>Мой аккаунт</Link>
              <button className="link-button" onClick={logout} type="button">Выйти</button>
            </>
          ) : (
            <>
              <Link to="/login">Войти</Link>
              <Link className="nav-primary" to="/register">Стать продавцом</Link>
            </>
          )}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  )
}
