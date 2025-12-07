import { useState } from 'react'
import { Product } from '../../types/schema'
import api from '../../lib/api'
import { formatValueWithUnit, formatPrice, getProxiedImageUrl } from '../../lib/format'
import DiscoveryConfigModal, { DiscoveryConfig } from './DiscoveryConfigModal'

interface MatchCandidatesProps {
  product: Product
  candidates: any[]
  discoveredAt?: string
  onDiscover: (config: DiscoveryConfig) => Promise<void>
  onApprove: (candidate: any) => void
  onManualLink: () => void
}

export default function MatchCandidates({
  product,
  candidates,
  discoveredAt,
  onDiscover,
  onApprove,
  onManualLink
}: MatchCandidatesProps) {
  const [discovering, setDiscovering] = useState(false)
  const [approvingUrls, setApprovingUrls] = useState<Set<string>>(new Set())
  const [showConfigModal, setShowConfigModal] = useState(false)

  // Ensure candidates is always an array
  const safeCandidates = Array.isArray(candidates) ? candidates : []

  const handleDiscoverClick = () => {
    console.log('Discover button clicked, opening modal')
    setShowConfigModal(true)
  }

  const handleDiscoverConfirm = async (config: DiscoveryConfig) => {
    setShowConfigModal(false)
    setDiscovering(true)
    try {
      // Call the parent's discover handler which makes the API call and updates state
      await onDiscover(config)
    } catch (error) {
      console.error('Discovery failed:', error)
      // Error is already handled in parent component
    } finally {
      setDiscovering(false)
    }
  }

  // Get product image URL from image_url field or from data.image_url or data.image
  const productImageUrl = (product as any).image_url || product.data?.image_url || product.data?.image
  const proxiedProductImageUrl = getProxiedImageUrl(productImageUrl)

  return (
    <div className="p-8">
      <div className="mb-8 flex justify-between items-start">
        <div className="flex items-center gap-4">
          {proxiedProductImageUrl && (
            <div className="w-20 h-20 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0 flex items-center justify-center">
              <img
                src={proxiedProductImageUrl}
                alt={product.name}
                className="w-full h-full object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
          )}
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Potential Matches for {product.name}
            </h1>
            <p className="text-slate-500 mt-1">
              {safeCandidates.length > 0
                ? `AI has found ${safeCandidates.length} potential competitors for you to review.`
                : 'Click "Discover Competitors" to find matches.'}
            </p>
            {discoveredAt && (
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <span className="material-symbols-outlined text-sm">schedule</span>
                <span>Discovered {new Date(discoveredAt).toLocaleString()}</span>
              </p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleDiscoverClick}
            disabled={discovering}
            className="flex items-center gap-2 bg-primary text-white text-sm font-semibold py-2 px-4 rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {discovering ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Discovering...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-xl">search</span>
                <span>Discover Competitors</span>
              </>
            )}
          </button>
          <button
            onClick={onManualLink}
            className="flex items-center gap-2 bg-white border border-slate-200 text-slate-800 text-sm font-semibold py-2 px-4 rounded-lg hover:bg-slate-50"
          >
            <span className="material-symbols-outlined text-xl">link</span>
            <span>Link Manually</span>
          </button>
        </div>
      </div>

      {discovering ? (
        <div className="flex flex-col items-center justify-center py-24">
          <div className="relative w-16 h-16 mb-4">
            <div className="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-slate-600 font-medium text-lg">Discovering competitors...</p>
          <p className="text-slate-500 text-sm mt-2">This may take a few moments</p>
        </div>
      ) : safeCandidates.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          No candidates found yet. Click "Discover Competitors" to start.
        </div>
      ) : (
        <div className="space-y-4">
          {safeCandidates.map((candidate) => (
            <div
              key={candidate.url}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex gap-5"
            >
              {/* Product Image */}
              {(() => {
                const proxiedCandidateImageUrl = getProxiedImageUrl(candidate.image_url)
                return proxiedCandidateImageUrl && (
                  <div className="w-32 h-32 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0 flex items-center justify-center">
                    <img
                      src={proxiedCandidateImageUrl}
                      alt={candidate.product_name}
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        // Hide image on error
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                  </div>
                )
              })()}
              
              {/* Product Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-slate-500">{candidate.retailer_name}</span>
                </div>
                <h3 className="font-semibold text-slate-800 text-lg">{candidate.product_name}</h3>
                
                {/* Clickable URL */}
                <a
                  href={candidate.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 mt-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  <span className="material-symbols-outlined text-sm">open_in_new</span>
                  <span>View Product</span>
                </a>
                
                <p className="text-primary font-bold text-2xl mt-2">
                  {formatPrice(candidate.extracted_data?.price)}
                </p>
                
                {/* Show other key fields with units */}
                {(() => {
                  const schemaToUse = candidate.schema || product.schema
                  const fields = schemaToUse?.fields || []
                  const fieldsWithData = fields.filter((field) => 
                    field.name !== 'price' && 
                    field.name !== 'name' &&
                    candidate.extracted_data?.[field.name] != null
                  )
                  
                  if (fieldsWithData.length === 0) {
                    return null
                  }
                  
                  return (
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      {fieldsWithData.map((field) => {
                        const fieldValue = candidate.extracted_data[field.name]
                        const formattedValue = formatValueWithUnit(fieldValue, field.name, schemaToUse)
                        return (
                          <div key={field.name} className="text-sm text-slate-600">
                            <span className="font-medium">{field.label}:</span>{' '}
                            <span>{formattedValue}</span>
                          </div>
                        )
                      })}
                    </div>
                  )
                })()}
              </div>
              
              {/* Confidence & Action */}
              <div className="flex flex-col justify-between items-end flex-shrink-0 w-48">
                <div className="w-full">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-600">Confidence</span>
                    <span className="font-bold text-lg">
                      {(candidate.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{ width: `${candidate.confidence_score * 100}%` }}
                    />
                  </div>
                </div>
                
                <button
                  onClick={async () => {
                    setApprovingUrls(prev => new Set(prev).add(candidate.url))
                    try {
                      await onApprove(candidate)
                    } finally {
                      setApprovingUrls(prev => {
                        const next = new Set(prev)
                        next.delete(candidate.url)
                        return next
                      })
                    }
                  }}
                  disabled={approvingUrls.has(candidate.url)}
                  className="w-full bg-primary text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {approvingUrls.has(candidate.url) ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Adding...</span>
                    </>
                  ) : (
                    <span>Approve & Monitor</span>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showConfigModal && (
        <DiscoveryConfigModal
          product={product}
          onClose={() => setShowConfigModal(false)}
          onConfirm={handleDiscoverConfirm}
        />
      )}
    </div>
  )
}

