import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { SellerForm } from '../components/SellerForm'
import { getApiErrorMessage } from '../lib/api'
import { getSeller, updateSeller } from '../lib/seller-api'
import { useAuthStore } from '../store/auth'
import type { Seller, SellerFormValues } from '../types/seller'

function Avatar({ name }: { name: string }) {
  return <div className="avatar" aria-hidden="true">{name.trim().charAt(0).toUpperCase() || 'П'}</div>
}

export function SellerAccountPage() {
  const { sellerId = '' } = useParams()
  const currentUserId = useAuthStore((state) => state.userId)
  const [seller, setSeller] = useState<Seller | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const isOwner = Boolean(currentUserId && currentUserId === sellerId)

  useEffect(() => {
    setLoading(true); setError('')
    getSeller(sellerId).then(setSeller).catch((requestError) => setError(getApiErrorMessage(requestError))).finally(() => setLoading(false))
  }, [sellerId])

  if (loading) return <div className="state-page" aria-live="polite">Загружаем аккаунт…</div>
  if (error || !seller) return <div className="state-page"><h1>Не удалось открыть аккаунт</h1><p>{error}</p><button className="button secondary" onClick={() => window.location.reload()}>Повторить</button></div>

  return (
    <section className="account-page">
      <div className="profile-card card">
        <div className="profile-main">
          <Avatar name={seller.company_name} />
          <div><p className="eyebrow">ПРОДАВЕЦ</p><h1>{seller.company_name}</h1><p className="seller-person">{[seller.last_name, seller.first_name, seller.middle_name].filter(Boolean).join(' ')}</p></div>
        </div>
        {isOwner && <Link className="button secondary edit-button" to="/account/edit">Редактировать аккаунт</Link>}
        <dl className="details-grid">
          <div><dt>Email</dt><dd><a href={`mailto:${seller.email}`}>{seller.email}</a></dd></div>
          <div><dt>Телефон</dt><dd><a href={`tel:${seller.phone}`}>{seller.phone}</a></dd></div>
        </dl>
      </div>
      <div className="products-section">
        <div><p className="eyebrow">КАТАЛОГ</p><h2>Товары продавца</h2></div>
        <div className="empty-products card"><div className="empty-icon">□</div><h3>Товары скоро появятся</h3><p>Здесь будет опубликован ассортимент продавца.</p></div>
      </div>
    </section>
  )
}

export function EditSellerPage() {
  const navigate = useNavigate()
  const userId = useAuthStore((state) => state.userId)
  const [seller, setSeller] = useState<Seller | null>(null)
  const [loadError, setLoadError] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (userId) getSeller(userId).then(setSeller).catch((error) => setLoadError(getApiErrorMessage(error)))
  }, [userId])

  if (!userId) return <Navigate to="/login" replace />
  if (loadError) return <div className="state-page"><h1>Не удалось загрузить данные</h1><p>{loadError}</p></div>
  if (!seller) return <div className="state-page">Загружаем данные…</div>

  const initialValues: SellerFormValues = {
    email: seller.email, first_name: seller.first_name, last_name: seller.last_name,
    middle_name: seller.middle_name ?? '', company_name: seller.company_name,
    phone: seller.phone, password: '', passwordConfirm: '',
  }
  const submit = async (values: SellerFormValues) => {
    setPending(true); setSubmitError('')
    try {
      await updateSeller(userId, values)
      navigate(`/sellers/${userId}`, { replace: true })
    } catch (error) { setSubmitError(getApiErrorMessage(error)) }
    finally { setPending(false) }
  }

  return <section className="edit-page"><div className="page-heading"><p className="eyebrow">НАСТРОЙКИ АККАУНТА</p><h1>Редактирование данных</h1><p>Измените сведения о компании или задайте новый пароль.</p></div><div className="card form-card"><SellerForm initialValues={initialValues} isEdit submitLabel="Сохранить изменения" pending={pending} serverError={submitError} onSubmit={submit} onCancel={() => navigate(`/sellers/${userId}`)} /></div></section>
}
