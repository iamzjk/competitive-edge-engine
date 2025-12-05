import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import api from '../lib/api'
import Layout from '../components/layout/Layout'
import AlertCards from '../components/dashboard/AlertCards'
import ListingsTable from '../components/dashboard/ListingsTable'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<any>(null)
  const [listings, setListings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [summaryRes, listingsRes] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/listings'),
      ])
      
      setSummary(summaryRes.data)
      setListings(listingsRes.data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <Layout onLogout={handleLogout}>
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-4xl font-black text-slate-900 mb-2">Dashboard</h1>
          <p className="text-slate-500">Last updated: {new Date().toLocaleString()}</p>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading...</div>
        ) : (
          <>
            {summary && <AlertCards summary={summary.summary} />}
            <ListingsTable listings={listings} />
          </>
        )}
      </div>
    </Layout>
  )
}

