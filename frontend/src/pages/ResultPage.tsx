import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import type { CaseSummaryResponse } from '@/lib/types'

export default function ResultPage() {
  const { caseReference } = useParams<{ caseReference: string }>()
  const [data, setData] = useState<CaseSummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      if (!caseReference) return
      try {
        const res = await fetch(`/api/v1/cases/${caseReference}`)
        if (!res.ok) {
          throw new Error('Failed to fetch case')
        }
        const json = await res.json()
        setData(json)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [caseReference])

  if (loading) {
    return (
      <div className="min-h-screen p-4 flex items-center justify-center">
        <p className="text-text-secondary">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen p-4 flex flex-col items-center justify-center gap-4">
        <p className="text-red-700">{error}</p>
        <Link to="/" className="text-accent hover:text-accent-hover">
          Back to home
        </Link>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen p-4">
      <main className="w-full max-w-[960px] mx-auto">
        <header className="mb-6">
          <Link to="/" className="text-sm text-accent hover:text-accent-hover mb-2 inline-block">
            New check
          </Link>
          <h1 className="text-2xl font-semibold text-text-primary">Case: {data.case_reference}</h1>
          <p className="text-sm text-text-secondary mt-1">
            Chain: {data.chain} | Status: {data.status}
          </p>
          {data.demo_notice && (
            <p className="mt-2 text-xs text-status-attention-text bg-status-attention-bg inline-block px-2 py-1 rounded-sm">
              {data.demo_notice}
            </p>
          )}
        </header>

        <section className="bg-surface border border-border rounded-md p-6 mb-4">
          <h2 className="text-lg font-semibold mb-2 text-text-primary">Summary</h2>
          <p className="text-text-secondary">{data.summary_text}</p>
          <p className="text-xs text-text-muted mt-3">{data.limitations.standing_statement}</p>
        </section>

        <section className="bg-surface border border-border rounded-md p-6 mb-4">
          <h2 className="text-lg font-semibold mb-2 text-text-primary">Confidence panel</h2>
          <div className="space-y-2 text-sm text-text-secondary">
            <div>Path evidence: {data.confidence_panel.path_evidence}</div>
            <div>Attribution confidence: {data.confidence_panel.attribution_confidence}</div>
            <div>Behavioral signals: {data.confidence_panel.behavioral_signals}</div>
            <div>Corroboration strength: {data.confidence_panel.corroboration_strength}</div>
          </div>
        </section>
      </main>
    </div>
  )
}
