declare module 'ethjs-util' {
  export function isAddress(address: string): boolean
  export function isChecksumAddress(address: string): boolean
  export function toChecksumAddress(address: string): string
}
