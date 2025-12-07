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
  const [recrawling, setRecrawling] = useState(false)
  const [debugInfo, setDebugInfo] = useState<any>(null)

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
      
      // Debug: log the first listing to see if image_url is present
      if (listingsRes.data.length > 0) {
        console.log('First listing data:', listingsRes.data[0])
        console.log('Image URL:', listingsRes.data[0].image_url)
      }
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

  const handleDebugImages = async () => {
    try {
      const response = await api.get('/dashboard/debug-images')
      setDebugInfo(response.data)
      console.log('Debug info:', response.data)
      alert(`Total listings: ${response.data.total}, With images: ${response.data.with_images}`)
    } catch (error: any) {
      console.error('Failed to get debug info:', error)
      alert(`Debug failed: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`)
    }
  }

  const testImageProxy = async () => {
    try {
      // Test with a known Amazon URL
      const testUrl = 'https://m.media-amazon.com/images/I/717+3dz-a3L.jpg'
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/images/proxy?url=${encodeURIComponent(testUrl)}`)
      if (response.ok) {
        alert('Image proxy is working!')
        console.log('Proxy response OK')
      } else {
        alert(`Image proxy failed: ${response.status}`)
        console.log('Proxy response failed:', response.status)
      }
    } catch (error: any) {
      alert(`Image proxy error: ${error.message}`)
      console.error('Proxy error:', error)
    }
  }

  const testImageDisplay = () => {
    // Temporarily modify the first listing to have a test image URL
    if (listings.length > 0) {
      const testListing = { ...listings[0], image_url: 'https://m.media-amazon.com/images/I/717+3dz-a3L' }
      setListings([testListing, ...listings.slice(1)])
      console.log('Added test image URL to first listing')
    }
  }

  const testImageExtraction = async () => {
    if (listings.length > 0) {
      console.log('Testing extraction for listing:', listings[0])
      console.log('Listing ID:', listings[0].id)
      console.log('API URL:', `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/dashboard/test-extract/${listings[0].id}`)
      try {
        const response = await api.get(`/dashboard/test-extract/${listings[0].id}`)
        console.log('Image extraction test:', response.data)
        alert(`Image extraction result: ${JSON.stringify(response.data, null, 2)}`)
      } catch (error: any) {
        console.error('Test extraction failed:', error)
        console.error('Error status:', error?.response?.status)
        console.error('Error headers:', error?.response?.headers)
        const errorMessage = error?.response?.data?.detail ||
                           error?.response?.data?.message ||
                           error?.response?.data ||
                           error?.message ||
                           'Unknown error'
        console.log('Full error response:', error?.response?.data)
        alert(`Test extraction failed (${error?.response?.status}): ${JSON.stringify(errorMessage)}`)
      }
    } else {
      alert('No listings to test extraction on')
    }
  }

  const handleRecrawl = async () => {
    if (!confirm('This will recrawl all competitor listings. This may take a few minutes. Continue?')) {
      return
    }

    setRecrawling(true)
    console.log('Starting recrawl...')
    try {
      const response = await api.post('/crawl/batch')
      console.log('Recrawl response:', response.data)
      alert(`Recrawl complete! ${response.data.message}`)
      // Reload dashboard data to show updated listings
      await loadDashboardData()
    } catch (error: any) {
      console.error('Failed to recrawl:', error)
      console.error('Error details:', error?.response?.data)
      alert(`Recrawl failed: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`)
    } finally {
      setRecrawling(false)
    }
  }

  return (
    <Layout onLogout={handleLogout}>
      <div className="p-8">
        <div className="mb-8 flex justify-between items-start">
          <div>
          <h1 className="text-4xl font-black text-slate-900 mb-2">Dashboard</h1>
          <p className="text-slate-500">Last updated: {new Date().toLocaleString()}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={testImageProxy}
              className="flex items-center gap-2 bg-blue-500 text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-blue-600"
            >
              <span>Test Proxy</span>
            </button>
            <button
              onClick={testImageDisplay}
              className="flex items-center gap-2 bg-green-500 text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-green-600"
            >
              <span>Test Display</span>
            </button>
            <button
              onClick={testImageExtraction}
              className="flex items-center gap-2 bg-purple-500 text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-purple-600"
            >
              <span>Test Extract</span>
            </button>
            <button
              onClick={handleDebugImages}
              className="flex items-center gap-2 bg-gray-500 text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-gray-600"
            >
              <span>Debug Images</span>
            </button>
            <button
              onClick={handleRecrawl}
              disabled={recrawling || loading}
              className="flex items-center gap-2 bg-primary text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {recrawling ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Recrawling...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-xl">refresh</span>
                  <span>Recrawl All</span>
                </>
              )}
            </button>
          </div>
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

