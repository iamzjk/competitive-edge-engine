import { formatValueWithUnit, getProxiedImageUrl } from '../../lib/format'
import { ProductSchema } from '../../types/schema'

interface ComparisonFlyoutProps {
  listing: any
  onClose: () => void
}

export default function ComparisonFlyout({ listing, onClose }: ComparisonFlyoutProps) {
  const comparison = listing.comparison || {}
  const fields = comparison.fields || {}
  const metrics = comparison.metrics || {}
  const schema: ProductSchema = listing.product_schema || { fields: [], metrics: [] }
  const myProduct = listing.my_product || {}
  const myProductImageUrl = getProxiedImageUrl(myProduct.image_url)
  const listingImageUrl = getProxiedImageUrl(listing.image_url)
  
  // Helper to get field label and unit
  const getFieldInfo = (fieldName: string) => {
    const field = schema.fields.find((f) => f.name === fieldName)
    return {
      label: field?.label || fieldName,
      unit: field?.unit
    }
  }
  
  // Helper to format value with unit
  const formatFieldValue = (value: any, fieldName: string) => {
    if (value === null || value === undefined) return 'N/A'
    return formatValueWithUnit(value, fieldName, schema)
  }

  return (
    <div className="fixed inset-0 bg-black/30 z-40">
      <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg">
        <div className="flex h-full w-full flex-col bg-background-light shadow-2xl">
          <div className="flex h-full grow flex-col">
            <div className="flex justify-between items-center gap-2 px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {listingImageUrl && (
                  <div className="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0 flex items-center justify-center">
                    <img
                      src={listingImageUrl}
                      alt={listing.product_name}
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                  </div>
                )}
                <div className="flex flex-col flex-1 min-w-0">
                  <h2 className="text-base font-bold text-gray-900 truncate">
                    {listing.product_name}
                  </h2>
                  <p className="text-sm text-gray-500">Sold by {listing.retailer_name}</p>
                  <a
                    href={listing.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 mt-1"
                  >
                    <span className="material-symbols-outlined text-sm">open_in_new</span>
                    <span>View Product</span>
                  </a>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-800 flex-shrink-0"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-5">
              {/* Product Images Comparison */}
              <div className="mb-4 flex gap-4">
                {myProductImageUrl && (
                  <div className="flex-1">
                    <div className="text-xs text-gray-500 mb-2">Your Product</div>
                    <div className="rounded-lg overflow-hidden bg-gray-100 aspect-square flex items-center justify-center">
                      <img
                        src={myProductImageUrl}
                        alt={myProduct.name || 'Your Product'}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                    </div>
                    {myProduct.name && (
                      <div className="text-sm font-medium text-gray-800 mt-2 truncate">{myProduct.name}</div>
                    )}
                  </div>
                )}
                {listingImageUrl && (
                  <div className="flex-1">
                    <div className="text-xs text-gray-500 mb-2">Competitor</div>
                    <div className="rounded-lg overflow-hidden bg-gray-100 aspect-square flex items-center justify-center">
                      <img
                        src={listingImageUrl}
                        alt={listing.product_name}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                    </div>
                    <div className="text-sm font-medium text-gray-800 mt-2 truncate">{listing.product_name}</div>
                  </div>
                )}
              </div>
              
              <div className="flex overflow-hidden rounded-lg border border-gray-200 bg-white">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-3 text-left font-medium text-gray-800 w-[40%]">
                        Metric
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-gray-800 w-[30%]">
                        Your Product
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-gray-800 w-[30%]">
                        Competitor
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {Object.entries(fields).map(([fieldName, fieldComp]: [string, any]) => {
                      const fieldInfo = getFieldInfo(fieldName)
                      return (
                      <tr key={fieldName}>
                          <td className="px-4 py-4 text-gray-600">{fieldInfo.label}</td>
                        <td className="px-4 py-4 text-right text-gray-800">
                            {formatFieldValue(fieldComp.user, fieldName)}
                        </td>
                        <td className="px-4 py-4 text-right text-gray-800">
                          <div
                            className={`flex items-center justify-end gap-1.5 ${
                              fieldComp.alert === 'red'
                                ? 'text-red-600'
                                : fieldComp.alert === 'yellow'
                                ? 'text-yellow-600'
                                : 'text-gray-800'
                            }`}
                          >
                            {fieldComp.alert && (
                              <span className="material-symbols-outlined text-base">
                                {fieldComp.alert === 'red' ? 'arrow_downward' : 'arrow_upward'}
                              </span>
                            )}
                              <span>{formatFieldValue(fieldComp.competitor, fieldName)}</span>
                          </div>
                        </td>
                      </tr>
                      )
                    })}
                    {Object.entries(metrics).map(([metricName, metricComp]: [string, any]) => {
                      const metric = schema.metrics?.find((m) => m.name === metricName)
                      const metricLabel = metric?.label || metricName
                      return (
                      <tr key={metricName}>
                          <td className="px-4 py-4 text-gray-600">{metricLabel}</td>
                        <td className="px-4 py-4 text-right text-gray-800">
                            {metricComp.user != null ? metricComp.user.toFixed(2) : 'N/A'}
                            {metric?.format === 'currency' && ' $'}
                        </td>
                        <td className="px-4 py-4 text-right text-gray-800">
                          <div
                            className={`flex items-center justify-end gap-1.5 ${
                              metricComp.alert === 'yellow' ? 'text-yellow-600' : 'text-gray-800'
                            }`}
                          >
                            {metricComp.alert && (
                              <span className="material-symbols-outlined text-base">
                                arrow_upward
                              </span>
                            )}
                              <span>
                                {metricComp.competitor != null ? metricComp.competitor.toFixed(2) : 'N/A'}
                                {metric?.format === 'currency' && ' $'}
                              </span>
                          </div>
                        </td>
                      </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex px-6 py-4 border-t border-gray-200">
              <button
                onClick={onClose}
                className="flex-1 bg-primary text-white py-3 px-5 rounded-lg font-bold hover:bg-primary/90"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

