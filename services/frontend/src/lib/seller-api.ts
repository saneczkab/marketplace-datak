import { api } from './api'
import type { AuthResponse, Seller, SellerFormValues } from '../types/seller'

export interface LoginPayload {
  email: string
  password: string
}

function toSellerPayload(values: SellerFormValues, includePassword: boolean) {
  return {
    email: values.email.trim().toLowerCase(),
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    middle_name: values.middle_name.trim() || null,
    company_name: values.company_name.trim(),
    phone: values.phone.trim(),
    ...(includePassword && values.password ? { password: values.password } : {}),
  }
}

export async function registerSeller(values: SellerFormValues): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', toSellerPayload(values, true))
  return data
}

export async function loginSeller(payload: LoginPayload): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', {
    email: payload.email.trim().toLowerCase(),
    password: payload.password,
  })
  return data
}

// Public endpoint by product requirement: no authentication is required to view a seller.
export async function getSeller(id: string): Promise<Seller> {
  const { data } = await api.get<Seller>(`/sellers/${encodeURIComponent(id)}`)
  return data
}

export async function updateSeller(id: string, values: SellerFormValues): Promise<Seller> {
  const { data } = await api.patch<Seller>(
    `/sellers/${encodeURIComponent(id)}`,
    toSellerPayload(values, Boolean(values.password)),
  )
  return data
}
