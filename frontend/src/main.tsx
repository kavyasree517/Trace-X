import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'

// Self-hosted so the interface renders identically without an external font
// request, and so no browsing metadata leaves the origin.
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'

import './styles/tokens.css'
import './styles/globals.css'

/**
 * Query client defaults.
 *
 * Retries are disabled for 4xx because a rejected address or a missing case will
 * fail again on every retry, and retrying only delays the error the reporter is
 * waiting for. 5xx gets a short retry because upstream chain data does recover.
 * Stale time is long so navigating back to a result does not refetch evidence the
 * server has already committed.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        const status = (error as { status?: number } | null)?.status
        if (typeof status === 'number' && status < 500) return false
        return failureCount < 2
      },
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

const container = document.getElementById('root')

if (!container) {
  throw new Error('Root element not found. The index document is missing #root.')
}

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)