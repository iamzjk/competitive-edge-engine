interface ComparisonFlyoutProps {
  listing: any
  onClose: () => void
}

export default function ComparisonFlyout({ listing, onClose }: ComparisonFlyoutProps) {
  const comparison = listing.comparison || {}
  const fields = comparison.fields || {}
  const metrics = comparison.metrics || {}

  return (
    <div className="fixed inset-0 bg-black/30 z-40">
      <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg">
        <div className="flex h-full w-full flex-col bg-background-light shadow-2xl">
          <div className="flex h-full grow flex-col">
            <div className="flex justify-between items-center gap-2 px-6 py-4 border-b border-gray-200">
              <div className="flex flex-col">
                <h2 className="text-base font-bold text-gray-900 truncate">
                  {listing.product_name}
                </h2>
                <p className="text-sm text-gray-500">Sold by {listing.retailer_name}</p>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-800"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-5">
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
                    {Object.entries(fields).map(([fieldName, fieldComp]: [string, any]) => (
                      <tr key={fieldName}>
                        <td className="px-4 py-4 text-gray-600">{fieldName}</td>
                        <td className="px-4 py-4 text-right text-gray-800">
                          {fieldComp.user}
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
                            <span>{fieldComp.competitor}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {Object.entries(metrics).map(([metricName, metricComp]: [string, any]) => (
                      <tr key={metricName}>
                        <td className="px-4 py-4 text-gray-600">{metricName}</td>
                        <td className="px-4 py-4 text-right text-gray-800">
                          {metricComp.user?.toFixed(2)}
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
                            <span>{metricComp.competitor?.toFixed(2)}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
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

