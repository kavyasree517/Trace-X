import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { copy } from '@/lib/copy'
import { isValidEthereumAddress, isValidTxHash } from '@/lib/validation'

export default function HomePage() {
  const navigate = useNavigate()
  const [address, setAddress] = useState('')
  const [txHash, setTxHash] = useState('')
  const [incidentDate, setIncidentDate] = useState('')
  const [precision, setPrecision] = useState('unknown')
  const [amount, setAmount] = useState('')
  const [asset, setAsset] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!isValidEthereumAddress(address)) {
      setError(copy.home.form.errors.invalidAddress)
      return
    }

    if (txHash && !isValidTxHash(txHash)) {
      setError(copy.home.form.errors.invalidTxHash)
      return
    }

    if (incidentDate) {
      const d = new Date(incidentDate)
      if (d > new Date()) {
        setError(copy.home.form.errors.futureDate)
        return
      }
    }

    setSubmitting(true)
    try {
      const res = await fetch('/api/v1/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: address.trim(),
          chain: 'ethereum',
          tx_hash: txHash.trim() || null,
          incident_date: incidentDate ? new Date(incidentDate).toISOString() : null,
          incident_date_precision: precision,
          reported_amount: amount || null,
          reported_asset: asset || null,
          consent_for_narrative_storage: false,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: {} }))
        throw new Error(err.error?.message || 'Failed to create case')
      }
      const data = await res.json()
      navigate(`/cases/${data.case_reference}`)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-4">
      <main className="w-full max-w-[960px] mt-16">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold text-text-primary">{copy.home.title}</h1>
          <p className="mt-2 text-text-secondary">{copy.home.description}</p>
          <p className="mt-2 text-sm text-text-muted">{copy.home.note}</p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="bg-surface border border-border rounded-md p-6 shadow-sm space-y-4"
        >
          <div>
            <label htmlFor="address" className="block text-sm font-medium text-text-primary mb-1">
              {copy.home.form.addressLabel}
            </label>
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder={copy.home.form.addressPlaceholder}
              className="w-full px-3 py-2 border border-border rounded-sm focus-ring font-mono"
              aria-describedby={error ? 'form-error' : undefined}
              aria-invalid={!!error}
            />
          </div>

          <div>
            <label htmlFor="chain" className="block text-sm font-medium text-text-primary mb-1">
              {copy.home.form.chainLabel}
            </label>
            <select
              id="chain"
              className="w-full px-3 py-2 border border-border rounded-sm focus-ring"
            >
              <option value="ethereum">{copy.home.form.chainEthereum}</option>
            </select>
          </div>

          <details className="border-t border-border pt-4">
            <summary className="cursor-pointer text-sm font-medium text-text-primary">
              {copy.home.form.additionalDetails}
            </summary>
            <div className="mt-4 space-y-4">
              <div>
                <label htmlFor="txHash" className="block text-sm font-medium text-text-primary mb-1">
                  {copy.home.form.txHashLabel}
                </label>
                <input
                  id="txHash"
                  type="text"
                  value={txHash}
                  onChange={(e) => setTxHash(e.target.value)}
                  placeholder={copy.home.form.txHashPlaceholder}
                  className="w-full px-3 py-2 border border-border rounded-sm focus-ring font-mono"
                />
              </div>

              <div>
                <label htmlFor="incidentDate" className="block text-sm font-medium text-text-primary mb-1">
                  {copy.home.form.incidentDateLabel}
                </label>
                <input
                  id="incidentDate"
                  type="date"
                  value={incidentDate}
                  onChange={(e) => setIncidentDate(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-sm focus-ring"
                />
                <select
                  value={precision}
                  onChange={(e) => setPrecision(e.target.value)}
                  className="mt-2 w-full px-3 py-2 border border-border rounded-sm focus-ring"
                >
                  <option value="unknown">Unknown</option>
                  <option value="approximate">Approximate</option>
                  <option value="day">Day</option>
                  <option value="exact">Exact</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="amount" className="block text-sm font-medium text-text-primary mb-1">
                    {copy.home.form.reportedAmountLabel}
                  </label>
                  <input
                    id="amount"
                    type="text"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-sm focus-ring"
                  />
                </div>
                <div>
                  <label htmlFor="asset" className="block text-sm font-medium text-text-primary mb-1">
                    {copy.home.form.reportedAssetLabel}
                  </label>
                  <input
                    id="asset"
                    type="text"
                    value={asset}
                    onChange={(e) => setAsset(e.target.value)}
                    placeholder="ETH"
                    className="w-full px-3 py-2 border border-border rounded-sm focus-ring"
                  />
                </div>
              </div>
            </div>
          </details>

          {error && (
            <div
              id="form-error"
              role="alert"
              aria-live="polite"
              className="text-sm text-red-700 bg-red-50 border border-red-200 p-3 rounded-sm"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-accent text-white px-4 py-2 rounded-sm hover:bg-accent-hover focus-ring disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? copy.home.form.submitting : copy.home.form.submit}
          </button>
        </form>

        <footer className="mt-8 text-center text-sm text-text-muted">
          <a href="/docs" className="hover:text-accent">
            {copy.home.linkLimitations}
          </a>
        </footer>
      </main>
    </div>
  )
}
