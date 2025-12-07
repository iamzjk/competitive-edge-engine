import { useState } from 'react'
import ComparisonFlyout from '../comparison/ComparisonFlyout'
import { formatPrice, getProxiedImageUrl } from '../../lib/format'

interface ListingsTableProps {
  listings: any[]
}

export default function ListingsTable({ listings }: ListingsTableProps) {
  const [selectedListing, setSelectedListing] = useState<any | null>(null)

  if (listings.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center text-slate-500">
        No competitor listings found. Start by discovering competitors for your products.
      </div>
    )
  }

  return (
    <>
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Product</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Retailer</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Price</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Last Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {listings.map((listing) => {
              const comparison = listing.comparison || {}
              const hasAlerts = Object.values(comparison.fields || {}).some(
                (f: any) => f.alert === 'red' || f.alert === 'yellow'
              )
              
              // Debug logging
              const proxiedImageUrl = getProxiedImageUrl(listing.image_url)
              console.log(`Listing ${listing.product_name}:`, {
                original_image_url: listing.image_url,
                proxied_image_url: proxiedImageUrl,
                has_image: !!listing.image_url
              })
              
              return (
                <tr
                  key={listing.id}
                  className={`cursor-pointer hover:bg-slate-50 ${
                    hasAlerts ? 'bg-red-50' : ''
                  }`}
                  onClick={() => setSelectedListing(listing)}
                >
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-3">
                      {proxiedImageUrl ? (
                        <div className="w-12 h-12 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0 flex items-center justify-center">
                          <img
                            src={proxiedImageUrl}
                            alt={listing.product_name}
                            className="w-full h-full object-contain"
                            onError={(e) => {
                              console.error(`Image failed to load: ${proxiedImageUrl}`)
                              e.currentTarget.style.display = 'none'
                            }}
                          />
                        </div>
                      ) : (
                        <div className="w-12 h-12 rounded-lg overflow-hidden bg-slate-200 flex-shrink-0 flex items-center justify-center">
                          <span className="material-symbols-outlined text-slate-400 text-xl">image</span>
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-slate-800 font-medium">{listing.product_name}</div>
                        <a
                          href={listing.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 mt-0.5"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <span className="material-symbols-outlined text-sm">open_in_new</span>
                          <span>View Product</span>
                        </a>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm text-slate-500">{listing.retailer_name}</td>
                  <td className="px-4 py-2 text-sm text-slate-500">
                    {formatPrice(listing.data?.price)}
                  </td>
                  <td className="px-4 py-2 text-sm text-slate-500">
                    {listing.last_crawled_at
                      ? new Date(listing.last_crawled_at).toLocaleString()
                      : 'Never'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {selectedListing && (
        <ComparisonFlyout
          listing={selectedListing}
          onClose={() => setSelectedListing(null)}
        />
      )}
    </>
  )
}

