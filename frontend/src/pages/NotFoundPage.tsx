import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 gap-4">
      <h1 className="text-2xl font-semibold text-text-primary">Page not found</h1>
      <Link to="/" className="text-accent hover:text-accent-hover">
        Return home
      </Link>
    </div>
  )
}
