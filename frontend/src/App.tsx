import { Route, Routes } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ResultPage from './pages/ResultPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/cases/:caseReference" element={<ResultPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
