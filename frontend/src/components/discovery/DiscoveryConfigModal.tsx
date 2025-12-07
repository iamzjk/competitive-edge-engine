import { useState } from 'react'
import { Product } from '../../types/schema'

interface DiscoveryConfigModalProps {
  product: Product
  onClose: () => void
  onConfirm: (config: DiscoveryConfig) => void
}

export interface DiscoveryConfig {
  searchQuery: string
  retailers: string[]
  maxResults: number
}

interface RetailerInfo {
  id: string
  name: string
  searchUrlTemplate: (query: string) => string
}

const RETAILERS: RetailerInfo[] = [
  {
    id: 'amazon',
    name: 'Amazon',
    searchUrlTemplate: (query) => `https://www.amazon.com/s?k=${query.replace(/ /g, '+')}`
  },
  {
    id: 'homedepot',
    name: 'Home Depot',
    searchUrlTemplate: (query) => `https://www.homedepot.com/s/${query.replace(/ /g, '%20')}`
  },
  {
    id: 'walmart',
    name: 'Walmart',
    searchUrlTemplate: (query) => `https://www.walmart.com/search?q=${query.replace(/ /g, '+')}`
  },
  {
    id: 'lowes',
    name: 'Lowes',
    searchUrlTemplate: (query) => `https://www.lowes.com/search?searchTerm=${query.replace(/ /g, '+')}`
  }
]

export default function DiscoveryConfigModal({
  product,
  onClose,
  onConfirm
}: DiscoveryConfigModalProps) {
  console.log('DiscoveryConfigModal rendered for product:', product.name)
  
  const [searchQuery, setSearchQuery] = useState(product.name)
  const [selectedRetailers, setSelectedRetailers] = useState<string[]>(
    RETAILERS.map(r => r.id)
  )
  const [maxResults, setMaxResults] = useState(5)

  const toggleRetailer = (retailerId: string) => {
    setSelectedRetailers(prev =>
      prev.includes(retailerId)
        ? prev.filter(id => id !== retailerId)
        : [...prev, retailerId]
    )
  }

  const handleConfirm = () => {
    if (selectedRetailers.length === 0) {
      alert('Please select at least one retailer')
      return
    }
    
    if (maxResults < 1 || maxResults > 20) {
      alert('Max results must be between 1 and 20')
      return
    }

    onConfirm({
      searchQuery,
      retailers: selectedRetailers,
      maxResults
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl m-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-slate-900">
              Configure Discovery
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full hover:bg-slate-100 text-slate-500"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>

          {/* Search Query */}
          <div className="mb-6">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Search Query
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            placeholder="Enter search query..."
          />
          <p className="text-xs text-slate-500 mt-1">
            This query will be used to search across selected retailers
          </p>
        </div>

        {/* Retailers Selection */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-slate-700 mb-3">
            Select Retailers
          </label>
          <div className="space-y-2">
            {RETAILERS.map((retailer) => {
              const isSelected = selectedRetailers.includes(retailer.id)
              return (
                <div key={retailer.id} className="border border-slate-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      id={`retailer-${retailer.id}`}
                      checked={isSelected}
                      onChange={() => toggleRetailer(retailer.id)}
                      className="mt-1 w-4 h-4 text-primary border-slate-300 rounded focus:ring-primary cursor-pointer"
                    />
                    <div className="flex-1 min-w-0">
                      <label
                        htmlFor={`retailer-${retailer.id}`}
                        className="font-medium text-slate-900 cursor-pointer block"
                      >
                        {retailer.name}
                      </label>
                      {isSelected && searchQuery && (
                        <div className="mt-2">
                          <p className="text-xs text-slate-500 mb-1">Search URL:</p>
                          <a
                            href={retailer.searchUrlTemplate(searchQuery)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-primary hover:text-primary/80 break-all flex items-center gap-1"
                          >
                            <span className="material-symbols-outlined text-sm">open_in_new</span>
                            <span className="break-all">{retailer.searchUrlTemplate(searchQuery)}</span>
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {selectedRetailers.length} retailer{selectedRetailers.length !== 1 ? 's' : ''} selected
          </p>
        </div>

        {/* Max Results */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Max Results per Retailer
          </label>
          <div className="flex items-center gap-4">
            <input
              type="number"
              min="1"
              max="20"
              value={maxResults}
              onChange={(e) => setMaxResults(parseInt(e.target.value) || 5)}
              className="w-24 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            <input
              type="range"
              min="1"
              max="20"
              value={maxResults}
              onChange={(e) => setMaxResults(parseInt(e.target.value))}
              className="flex-1"
            />
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Up to {maxResults} product{maxResults !== 1 ? 's' : ''} will be fetched from each retailer
            (Total: up to {maxResults * selectedRetailers.length} products)
          </p>
        </div>

        {/* Summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">Discovery Summary</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Query: <span className="font-medium">{searchQuery || '(empty)'}</span></li>
            <li>• Retailers: <span className="font-medium">{selectedRetailers.length}</span> selected</li>
            <li>• Max results: <span className="font-medium">{maxResults}</span> per retailer</li>
            <li>• Estimated products: <span className="font-medium">up to {maxResults * selectedRetailers.length}</span></li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!searchQuery.trim() || selectedRetailers.length === 0}
            className="px-6 py-2 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-xl">search</span>
            <span>Start Discovery</span>
          </button>
        </div>
        </div>
      </div>
    </div>
  )
}

