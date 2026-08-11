import { describe, expect, it } from 'vitest'
import { validateLogin, validateSellerForm } from './validation'
import type { SellerFormValues } from '../types/seller'

const validValues: SellerFormValues = {
  email: 'seller@example.com',
  first_name: 'Иван',
  last_name: 'Иванов',
  middle_name: '',
  company_name: 'Зелёный рынок',
  phone: '+7 999 000-00-00',
  password: 'password1',
  passwordConfirm: 'password1',
}

describe('validateSellerForm', () => {
  it('accepts a complete registration form', () => {
    expect(validateSellerForm(validValues)).toEqual({})
  })

  it('validates required fields, email, phone and password confirmation', () => {
    const errors = validateSellerForm({
      ...validValues,
      email: 'wrong',
      first_name: '',
      phone: 'abc',
      password: 'short',
      passwordConfirm: 'different',
    })
    expect(errors.email).toBeTruthy()
    expect(errors.first_name).toBeTruthy()
    expect(errors.phone).toBeTruthy()
    expect(errors.password).toBeTruthy()
    expect(errors.passwordConfirm).toBeTruthy()
  })

  it('allows an empty password while editing', () => {
    expect(validateSellerForm({ ...validValues, password: '', passwordConfirm: '' }, true)).toEqual({})
  })
})

describe('validateLogin', () => {
  it('requires a valid email and password', () => {
    expect(validateLogin('bad-email', '')).toEqual({
      email: 'Введите корректный email.',
      password: 'Введите пароль.',
    })
  })
})
