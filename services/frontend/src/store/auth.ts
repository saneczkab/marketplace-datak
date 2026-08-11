import { create } from 'zustand'
import type { AuthResponse } from '../types/seller'

const STORAGE_KEY = 'marketplace-datak-seller-auth'

type StoredAuth = Pick<AuthResponse, 'access_token' | 'refresh_token' | 'user_id'>

function readStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as StoredAuth) : null
  } catch {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  userId: string | null
  setAuth: (auth: AuthResponse) => void
  clearAuth: () => void
}

const stored = readStoredAuth()

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: stored?.access_token ?? null,
  refreshToken: stored?.refresh_token ?? null,
  userId: stored?.user_id ?? null,
  setAuth: (auth) => {
    const value: StoredAuth = {
      access_token: auth.access_token,
      refresh_token: auth.refresh_token,
      user_id: auth.user_id,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
    set({
      accessToken: auth.access_token,
      refreshToken: auth.refresh_token,
      userId: auth.user_id,
    })
  },
  clearAuth: () => {
    localStorage.removeItem(STORAGE_KEY)
    set({ accessToken: null, refreshToken: null, userId: null })
  },
}))
