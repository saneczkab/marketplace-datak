import type { SellerFormErrors, SellerFormValues } from '../types/seller'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^\+?[0-9 ()-]{7,20}$/

export function validateLogin(email: string, password: string) {
  const errors: { email?: string; password?: string } = {}
  if (!email.trim()) errors.email = 'Введите email.'
  else if (!EMAIL_RE.test(email.trim())) errors.email = 'Введите корректный email.'
  if (!password) errors.password = 'Введите пароль.'
  return errors
}

export function validateSellerForm(values: SellerFormValues, isEdit = false): SellerFormErrors {
  const errors: SellerFormErrors = {}
  if (!values.email.trim()) errors.email = 'Введите email.'
  else if (!EMAIL_RE.test(values.email.trim())) errors.email = 'Введите корректный email.'
  if (!values.first_name.trim()) errors.first_name = 'Введите имя.'
  if (!values.last_name.trim()) errors.last_name = 'Введите фамилию.'
  if (!values.company_name.trim()) errors.company_name = 'Введите наименование компании.'
  if (!values.phone.trim()) errors.phone = 'Введите телефон.'
  else if (!PHONE_RE.test(values.phone.trim())) errors.phone = 'Введите корректный номер телефона.'

  if (!isEdit && !values.password) errors.password = 'Введите пароль.'
  else if (values.password && values.password.length < 8) errors.password = 'Пароль должен содержать минимум 8 символов.'
  if (values.password !== values.passwordConfirm) errors.passwordConfirm = 'Пароли не совпадают.'
  return errors
}
