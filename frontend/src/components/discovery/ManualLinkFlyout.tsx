import { useState } from 'react'
import { Product } from '../../types/schema'
import api from '../../lib/api'

interface ManualLinkFlyoutProps {
  product: Product
  onClose: () => void
  onSuccess: () => void
}

export default function ManualLinkFlyout({ product, onClose, onSuccess }: ManualLinkFlyoutProps) {
  const [url, setUrl] = useState('')
  const [retailerName, setRetailerName] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // First crawl the URL
      const crawlResponse = await api.post('/crawl/single', {
        product_id: product.id,
        url,
        retailer_name: retailerName || 'Unknown'
      })

      // Then create competitor listing
      await api.post('/competitors/manual', {
        my_product_id: product.id,
        url,
        retailer_name: retailerName || 'Unknown',
        product_name: 'Extracted Product', // Will be updated after crawl
        data: crawlResponse.data.extracted_data,
        image_url: crawlResponse.data.image_url || ''
      })

      onSuccess()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to add competitor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 z-20">
      <div className="absolute inset-y-0 right-0 w-full max-w-md bg-white shadow-2xl flex flex-col">
        <div className="p-6 border-b border-slate-200">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-900">Link Competitor Manually</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-slate-100 text-slate-500"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex-1 overflow-y-auto">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Product: {product.name}
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Competitor Product URL <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.example.com/product-page"
                required
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Retailer Name
              </label>
              <input
                type="text"
                value={retailerName}
                onChange={(e) => setRetailerName(e.target.value)}
                placeholder="e.g., Amazon, Home Depot"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-4">
            <button
              type="button"
              onClick={onClose}
              className="text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-slate-100 text-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-primary text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Crawling...' : 'Crawl and Add Listing'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

