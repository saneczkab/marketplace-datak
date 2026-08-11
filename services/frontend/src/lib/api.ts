import axios, { AxiosError } from 'axios'
import { useAuthStore } from '../store/auth'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && useAuthStore.getState().accessToken) {
      useAuthStore.getState().clearAuth()
      window.dispatchEvent(new Event('seller-session-expired'))
    }
    return Promise.reject(error)
  },
)

interface ApiValidationError {
  msg?: string
  loc?: Array<string | number>
}

export function getApiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return 'Произошла непредвиденная ошибка. Попробуйте ещё раз.'
  if (!error.response) return 'Не удалось подключиться к серверу. Проверьте интернет-соединение и повторите попытку.'

  const data = error.response.data as { detail?: string | ApiValidationError[]; message?: string } | undefined
  if (typeof data?.detail === 'string') return data.detail
  if (Array.isArray(data?.detail)) return data.detail.map((item) => item.msg).filter(Boolean).join('. ')
  if (data?.message) return data.message

  if (error.response.status === 401) return 'Неверный email или пароль.'
  if (error.response.status === 403) return 'У вас нет прав для выполнения этого действия.'
  if (error.response.status === 404) return 'Аккаунт продавца не найден.'
  if (error.response.status === 409) return 'Аккаунт с таким email уже существует.'
  return 'Сервер не смог обработать запрос. Попробуйте ещё раз позже.'
}
