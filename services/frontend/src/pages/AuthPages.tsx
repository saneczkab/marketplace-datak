import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { getApiErrorMessage } from '../lib/api'
import { loginSeller, registerSeller } from '../lib/seller-api'
import { validateLogin } from '../lib/validation'
import { SellerForm } from '../components/SellerForm'
import { useAuthStore } from '../store/auth'
import type { SellerFormValues } from '../types/seller'

export function RegisterPage() {
  const navigate = useNavigate()
  const { userId, setAuth } = useAuthStore()
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  if (userId) return <Navigate to={`/sellers/${userId}`} replace />

  const submit = async (values: SellerFormValues) => {
    setPending(true); setError('')
    try {
      const auth = await registerSeller(values)
      setAuth(auth)
      navigate(`/sellers/${auth.user_id}`, { replace: true })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    } finally { setPending(false) }
  }

  return (
    <section className="auth-page">
      <div className="auth-heading"><p className="eyebrow">КАБИНЕТ ПРОДАВЦА</p><h1>Создайте аккаунт продавца</h1><p>Добавьте данные компании — подтверждение регистрации не требуется.</p></div>
      <div className="card form-card"><SellerForm submitLabel="Зарегистрироваться" pending={pending} serverError={error} onSubmit={submit} /><p className="form-footnote">Уже есть аккаунт? <Link to="/login">Войти</Link></p></div>
    </section>
  )
}

export function LoginPage() {
  const navigate = useNavigate()
  const { userId, setAuth } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({})
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  if (userId) return <Navigate to={`/sellers/${userId}`} replace />

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const nextErrors = validateLogin(email, password)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return
    setPending(true); setError('')
    try {
      const auth = await loginSeller({ email, password })
      setAuth(auth)
      navigate(`/sellers/${auth.user_id}`, { replace: true })
    } catch (requestError) { setError(getApiErrorMessage(requestError)) }
    finally { setPending(false) }
  }

  return (
    <section className="login-page">
      <div className="card login-card">
        <p className="eyebrow">КАБИНЕТ ПРОДАВЦА</p><h1>Вход в аккаунт</h1><p>Управляйте профилем компании и товарами.</p>
        <form onSubmit={submit} noValidate>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <label className="field"><span>Email</span><input type="email" autoComplete="email" value={email} onChange={(e) => { setEmail(e.target.value); setErrors((v) => ({ ...v, email: undefined })) }} aria-invalid={Boolean(errors.email)} />{errors.email && <span className="field-error">{errors.email}</span>}</label>
          <label className="field"><span>Пароль</span><input type="password" autoComplete="current-password" value={password} onChange={(e) => { setPassword(e.target.value); setErrors((v) => ({ ...v, password: undefined })) }} aria-invalid={Boolean(errors.password)} />{errors.password && <span className="field-error">{errors.password}</span>}</label>
          <button className="button primary full" type="submit" disabled={pending}>{pending ? 'Входим…' : 'Войти'}</button>
        </form>
        <p className="form-footnote">Нет аккаунта? <Link to="/register">Зарегистрироваться</Link></p>
      </div>
    </section>
  )
}
