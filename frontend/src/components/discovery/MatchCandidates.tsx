import { useState, useEffect } from 'react'
import { Product } from '../../types/schema'
import api from '../../lib/api'

interface MatchCandidatesProps {
  product: Product
  candidates: any[]
  onDiscover: () => void
  onApprove: (candidate: any) => void
  onManualLink: () => void
}

export default function MatchCandidates({
  product,
  candidates,
  onDiscover,
  onApprove,
  onManualLink
}: MatchCandidatesProps) {
  const [discovering, setDiscovering] = useState(false)

  const handleDiscover = async () => {
    setDiscovering(true)
    try {
      await api.post(`/matches/discover/${product.id}`)
      onDiscover()
    } catch (error) {
      console.error('Discovery failed:', error)
      alert('Discovery failed. Please try again.')
    } finally {
      setDiscovering(false)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Potential Matches for {product.name}
          </h1>
          <p className="text-slate-500 mt-1">
            {candidates.length > 0
              ? `AI has found ${candidates.length} potential competitors for you to review.`
              : 'Click "Discover Competitors" to find matches.'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleDiscover}
            disabled={discovering}
            className="flex items-center gap-2 bg-primary text-white text-sm font-semibold py-2 px-4 rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            {discovering ? 'Discovering...' : 'Discover Competitors'}
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

      {candidates.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          No candidates found yet. Click "Discover Competitors" to start.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {candidates.map((candidate, index) => (
            <div
              key={index}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-5"
            >
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-slate-500">{candidate.retailer_name}</span>
                </div>
                <h3 className="font-semibold text-slate-800">{candidate.product_name}</h3>
                <p className="text-slate-500 font-bold text-lg mt-1">
                  ${candidate.extracted_data?.price || 'N/A'}
                </p>
              </div>

              <div className="mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Confidence</span>
                  <span className="font-bold text-base">
                    {(candidate.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-primary h-2 rounded-full"
                    style={{ width: `${candidate.confidence_score * 100}%` }}
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => onApprove(candidate)}
                  className="flex-1 bg-primary text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-primary/90"
                >
                  Approve & Monitor
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

