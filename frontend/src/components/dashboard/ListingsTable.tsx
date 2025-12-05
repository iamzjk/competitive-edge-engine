import { useState } from 'react'
import ComparisonFlyout from '../comparison/ComparisonFlyout'

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
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Product Name</th>
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
              
              return (
                <tr
                  key={listing.id}
                  className={`cursor-pointer hover:bg-slate-50 ${
                    hasAlerts ? 'bg-red-50' : ''
                  }`}
                  onClick={() => setSelectedListing(listing)}
                >
                  <td className="px-4 py-2 text-sm text-slate-800">{listing.product_name}</td>
                  <td className="px-4 py-2 text-sm text-slate-500">{listing.retailer_name}</td>
                  <td className="px-4 py-2 text-sm text-slate-500">
                    ${listing.data?.price || 'N/A'}
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

