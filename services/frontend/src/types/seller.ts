export interface Seller {
  id: string
  email: string
  first_name: string
  last_name: string
  middle_name?: string | null
  company_name: string
  phone: string
  created_at?: string
  updated_at?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user_id: string
}

export interface SellerFormValues {
  email: string
  first_name: string
  last_name: string
  middle_name: string
  company_name: string
  phone: string
  password: string
  passwordConfirm: string
}

export type SellerFormErrors = Partial<Record<keyof SellerFormValues, string>>
