import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'

interface LayoutProps {
  children: ReactNode
  onLogout: () => void
}

export default function Layout({ children, onLogout }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="flex h-screen">
      <aside className="w-64 border-r border-slate-200 bg-white p-4 flex flex-col">
        <div className="mb-8">
          <h2 className="text-xl font-bold text-slate-900">Competitive Edge</h2>
        </div>

        <nav className="flex-1 space-y-2">
          <Link
            to="/dashboard"
            className={`flex items-center gap-3 px-3 py-2 rounded-lg ${
              location.pathname === '/dashboard'
                ? 'bg-blue-50 text-primary'
                : 'text-slate-700 hover:bg-slate-100'
            }`}
          >
            <span className="material-symbols-outlined">dashboard</span>
            <span className="text-sm font-medium">Dashboard</span>
          </Link>

          <Link
            to="/discovery"
            className={`flex items-center gap-3 px-3 py-2 rounded-lg ${
              location.pathname === '/discovery'
                ? 'bg-blue-50 text-primary'
                : 'text-slate-700 hover:bg-slate-100'
            }`}
          >
            <span className="material-symbols-outlined">travel_explore</span>
            <span className="text-sm font-medium">Competitor Discovery</span>
          </Link>
        </nav>

        <div className="mt-auto">
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-100"
          >
            <span className="material-symbols-outlined">logout</span>
            <span className="text-sm font-medium">Logout</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-hidden bg-background-light">
        {children}
      </main>
    </div>
  )
}

