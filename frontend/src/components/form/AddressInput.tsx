/**
 * Address input with blur-time validation.
 *
 * Validation runs on blur rather than on every keystroke. Checking as the user
 * types marks a partially typed address invalid, which is a false accusation
 * against correct input; blur is the moment where "I have finished typing" is
 * actually true. After the first blur the field re-validates on change, so the
 * error clears as soon as it is fixed without waiting for another blur.
 *
 * The component reports validity upward through `onValidate` and renders no
 * error of its own. The parent owns the message, which is what keeps the error
 * inside the `aria-describedby` chain that `FormField` establishes.
 */

import { validateAddress, type AddressValidationCode } from '@/lib/validation'
import { copy } from '@/lib/copy'

interface AddressInputProps {
  value: string
  onChange: (value: string) => void
  /** Receives an undefined message when the value is acceptable. */
  onValidate: (message: string | undefined) => void
  /** True when the parent is currently showing a message for this field. */
  invalid: boolean
  id: string
  'aria-describedby'?: string
  disabled?: boolean
}

export function addressErrorMessage(code: AddressValidationCode): string | undefined {
  switch (code) {
    case 'required':
      return copy.home.form.errors.addressRequired
    case 'invalid_format':
      return copy.home.form.errors.invalidAddress
    case 'bad_checksum':
      return copy.home.form.errors.mixedCaseAddress
    default:
      return undefined
  }
}

export function AddressInput({
  value,
  onChange,
  onValidate,
  invalid,
  id,
  'aria-describedby': describedBy,
  disabled = false,
}: AddressInputProps) {
  const validate = (next: string) => {
    // An untouched empty field is not reported here. The required check happens
    // on submit, so an empty optional-looking input never shows an error.
    if (next.trim().length === 0) {
      onValidate(undefined)
      return
    }
    onValidate(addressErrorMessage(validateAddress(next).code))
  }

  return (
    <input
      id={id}
      type="text"
      inputMode="text"
      autoComplete="off"
      autoCorrect="off"
      autoCapitalize="off"
      spellCheck={false}
      required
      value={value}
      disabled={disabled}
      onChange={(event) => {
        onChange(event.target.value)
        validate(event.target.value)
      }}
      onBlur={(event) => validate(event.target.value)}
      placeholder={copy.home.form.addressPlaceholder}
      aria-describedby={describedBy}
      aria-invalid={invalid}
      aria-required="true"
      className="control font-mono"
    />
  )
}

export type { AddressInputProps }