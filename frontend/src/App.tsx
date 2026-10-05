import { Route, Routes } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { ResultPage } from './pages/ResultPage'
import { NotFoundPage } from './pages/NotFoundPage'

/**
 * Routes.
 *
 * `*` catches every unmatched path so a mistyped case reference lands on a page
 * that explains the reference format, rather than on a blank screen. Case
 * references are unguessable access tokens, so the URL is the whole authorisation
 * model here; there is no per-user routing to define.
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/cases/:caseReference" element={<ResultPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}