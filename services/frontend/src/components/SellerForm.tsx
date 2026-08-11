import { useState, type FormEvent } from 'react'
import { validateSellerForm } from '../lib/validation'
import type { SellerFormErrors, SellerFormValues } from '../types/seller'

export const emptySellerForm: SellerFormValues = {
  email: '', first_name: '', last_name: '', middle_name: '',
  company_name: '', phone: '', password: '', passwordConfirm: '',
}

interface SellerFormProps {
  initialValues?: SellerFormValues
  isEdit?: boolean
  submitLabel: string
  pending: boolean
  serverError?: string
  onSubmit: (values: SellerFormValues) => Promise<void>
  onCancel?: () => void
}

interface FieldProps {
  name: keyof SellerFormValues
  label: string
  type?: string
  autoComplete?: string
  placeholder?: string
  optional?: boolean
  value: string
  error?: string
  onChange: (name: keyof SellerFormValues, value: string) => void
}

function Field({ name, label, type = 'text', optional, error, onChange, ...props }: FieldProps) {
  const errorId = `${name}-error`
  return (
    <label className="field">
      <span>{label}{optional && <small> Необязательно</small>}</span>
      <input
        {...props}
        name={name}
        type={type}
        onChange={(event) => onChange(name, event.target.value)}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
      />
      {error && <span className="field-error" id={errorId}>{error}</span>}
    </label>
  )
}

export function SellerForm({ initialValues = emptySellerForm, isEdit = false, submitLabel, pending, serverError, onSubmit, onCancel }: SellerFormProps) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState<SellerFormErrors>({})

  const update = (name: keyof SellerFormValues, value: string) => {
    setValues((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: undefined }))
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const nextErrors = validateSellerForm(values, isEdit)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return
    await onSubmit(values)
  }

  return (
    <form className="seller-form" onSubmit={submit} noValidate>
      {serverError && <div className="alert alert-error" role="alert">{serverError}</div>}
      <div className="form-grid">
        <Field name="company_name" label="Наименование компании" autoComplete="organization" value={values.company_name} error={errors.company_name} onChange={update} />
        <Field name="email" label="Email" type="email" autoComplete="email" value={values.email} error={errors.email} onChange={update} />
        <Field name="last_name" label="Фамилия" autoComplete="family-name" value={values.last_name} error={errors.last_name} onChange={update} />
        <Field name="first_name" label="Имя" autoComplete="given-name" value={values.first_name} error={errors.first_name} onChange={update} />
        <Field name="middle_name" label="Отчество" autoComplete="additional-name" optional value={values.middle_name} error={errors.middle_name} onChange={update} />
        <Field name="phone" label="Телефон" type="tel" autoComplete="tel" placeholder="+7 999 000-00-00" value={values.phone} error={errors.phone} onChange={update} />
        <Field name="password" label={isEdit ? 'Новый пароль' : 'Пароль'} type="password" autoComplete="new-password" optional={isEdit} value={values.password} error={errors.password} onChange={update} />
        <Field name="passwordConfirm" label="Повторите пароль" type="password" autoComplete="new-password" optional={isEdit} value={values.passwordConfirm} error={errors.passwordConfirm} onChange={update} />
      </div>
      <div className="form-actions">
        {onCancel && <button className="button secondary" type="button" onClick={onCancel} disabled={pending}>Отмена</button>}
        <button className="button primary" type="submit" disabled={pending}>{pending ? 'Сохраняем…' : submitLabel}</button>
      </div>
    </form>
  )
}
