import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import api from '../lib/api'
import Layout from '../components/layout/Layout'
import ProductList from '../components/discovery/ProductList'
import MatchCandidates from '../components/discovery/MatchCandidates'
import AddProductModal from '../components/discovery/AddProductModal'
import ManualLinkFlyout from '../components/discovery/ManualLinkFlyout'
import { Product } from '../types/schema'

export default function DiscoveryPage() {
  const navigate = useNavigate()
  const [products, setProducts] = useState<Product[]>([])
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [candidates, setCandidates] = useState<any[]>([])
  const [showAddModal, setShowAddModal] = useState(false)
  const [showManualLink, setShowManualLink] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProducts()
  }, [])

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

  const handleDiscover = async (productId: string) => {
    try {
      const response = await api.post(`/matches/discover/${productId}`)
      setCandidates(response.data)
    } catch (error) {
      console.error('Failed to discover competitors:', error)
    }
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  return (
    <Layout onLogout={handleLogout}>
      <div className="flex h-screen">
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
              onDiscover={() => handleDiscover(selectedProduct.id)}
              onApprove={async (candidate) => {
                try {
                  await api.post('/matches/approve', {
                    product_id: selectedProduct.id,
                    ...candidate
                  })
                  alert('Competitor added to monitoring!')
                  loadProducts()
                } catch (error) {
                  console.error('Failed to approve candidate:', error)
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

