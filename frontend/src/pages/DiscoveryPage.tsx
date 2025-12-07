import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import api from '../lib/api'
import Layout from '../components/layout/Layout'
import ProductList from '../components/discovery/ProductList'
import MatchCandidates from '../components/discovery/MatchCandidates'
import AddProductModal from '../components/discovery/AddProductModal'
import ManualLinkFlyout from '../components/discovery/ManualLinkFlyout'
import { DiscoveryConfig } from '../components/discovery/DiscoveryConfigModal'
import { Product } from '../types/schema'

const CACHE_KEY = 'discovery_candidates_cache'
const CACHE_VERSION = 'v1'

export default function DiscoveryPage() {
  const navigate = useNavigate()
  const [products, setProducts] = useState<Product[]>([])
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [candidates, setCandidates] = useState<any[]>([])
  const [showAddModal, setShowAddModal] = useState(false)
  const [showManualLink, setShowManualLink] = useState(false)
  const [loading, setLoading] = useState(true)

  // Load cached candidates from sessionStorage
  const loadCachedCandidates = (productId: string): any[] => {
    try {
      const cached = sessionStorage.getItem(CACHE_KEY)
      if (cached) {
        const cache = JSON.parse(cached)
        
        // Check cache version and clear if outdated
        if (cache.version !== CACHE_VERSION) {
          console.log('Cache version mismatch, clearing cache')
          sessionStorage.removeItem(CACHE_KEY)
          return []
        }
        
        const data = cache.data?.[productId]
        // Ensure we return an array
        if (Array.isArray(data)) {
          return data
        }
        console.warn('Cached data is not an array:', data)
      }
    } catch (error) {
      console.error('Failed to load cached candidates:', error)
      // Clear corrupted cache
      sessionStorage.removeItem(CACHE_KEY)
    }
    return []
  }

  // Save candidates to sessionStorage
  const saveCachedCandidates = (productId: string, candidates: any[]) => {
    try {
      const cached = sessionStorage.getItem(CACHE_KEY)
      let cache = cached ? JSON.parse(cached) : { version: CACHE_VERSION, data: {} }
      
      // Ensure cache has correct structure
      if (!cache.version || !cache.data) {
        cache = { version: CACHE_VERSION, data: {} }
      }
      
      cache.data[productId] = candidates
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(cache))
    } catch (error) {
      console.error('Failed to save cached candidates:', error)
      // Clear corrupted cache
      sessionStorage.removeItem(CACHE_KEY)
    }
  }

  useEffect(() => {
    loadProducts()
  }, [])

  // Load cached candidates when product selection changes
  useEffect(() => {
    if (selectedProduct) {
      const cached = loadCachedCandidates(selectedProduct.id)
      setCandidates(cached)
    } else {
      setCandidates([])
    }
  }, [selectedProduct])

  const loadProducts = async () => {
    try {
      const response = await api.get('/products')
      setProducts(response.data)
    } catch (error) {
      console.error('Failed to load products:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDiscover = async (productId: string, config: DiscoveryConfig) => {
    try {
      const response = await api.post(`/matches/discover/${productId}`, config)
      console.log('Discovery API response:', response.data)
      
      // Ensure we have an array
      let discoveredCandidates = response.data
      if (!Array.isArray(discoveredCandidates)) {
        console.warn('API returned non-array data:', discoveredCandidates)
        discoveredCandidates = []
      }
      
      // Save to sessionStorage cache
      saveCachedCandidates(productId, discoveredCandidates)
      
      // Update current candidates if this product is selected
      if (selectedProduct?.id === productId) {
        setCandidates(discoveredCandidates)
      }
      
      if (discoveredCandidates.length === 0) {
        alert('No matches found. This could be due to:\n- Search queries not returning results\n- Crawling failures\n- Extraction errors\n\nCheck the backend logs for more details.')
      }
    } catch (error: any) {
      console.error('Failed to discover competitors:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Unknown error occurred'
      alert(`Discovery failed: ${errorMessage}`)
      throw error // Re-throw to let the component handle the error state
    }
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <Layout onLogout={handleLogout}>
      <div className="flex h-full">
        <ProductList
          products={products}
          selectedProduct={selectedProduct}
          onSelectProduct={setSelectedProduct}
          onAddProduct={() => setShowAddModal(true)}
          loading={loading}
        />
        
        <div className="flex-1 overflow-y-auto bg-background-light">
          {selectedProduct ? (
            <MatchCandidates
              product={selectedProduct}
              candidates={candidates}
              onDiscover={async (config) => await handleDiscover(selectedProduct.id, config)}
              onApprove={async (candidate) => {
                try {
                  await api.post('/matches/approve', {
                    product_id: selectedProduct.id,
                    url: candidate.url,
                    retailer_name: candidate.retailer_name,
                    product_name: candidate.product_name,
                    extracted_data: candidate.extracted_data
                  })
                  alert('Competitor added to monitoring!')
                  loadProducts()
                } catch (error: any) {
                  console.error('Failed to approve candidate:', error)
                  const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to approve candidate. Please try again.'
                  alert(`Error: ${errorMessage}`)
                }
              }}
              onManualLink={() => setShowManualLink(true)}
            />
          ) : (
            <div className="p-8 text-center text-slate-500">
              Select a product to discover competitors
            </div>
          )}
        </div>

        {showAddModal && (
          <AddProductModal
            onClose={() => setShowAddModal(false)}
            onSuccess={() => {
              setShowAddModal(false)
              loadProducts()
            }}
          />
        )}

        {showManualLink && selectedProduct && (
          <ManualLinkFlyout
            product={selectedProduct}
            onClose={() => setShowManualLink(false)}
            onSuccess={() => {
              setShowManualLink(false)
              loadProducts()
            }}
          />
        )}
      </div>
    </Layout>
  )
}

