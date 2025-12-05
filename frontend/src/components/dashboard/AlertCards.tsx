interface AlertCardsProps {
  summary: {
    price_drops: { count: number; percentage_change: number }
    spec_disadvantages: { count: number; percentage_change: number }
    price_increases: { count: number; percentage_change: number }
  }
}

export default function AlertCards({ summary }: AlertCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <p className="text-slate-700 text-base font-medium mb-2">Price Drops</p>
        <p className="text-red-500 text-3xl font-bold">{summary.price_drops.count}</p>
        <p className="text-red-500 text-base font-medium">
          {summary.price_drops.percentage_change.toFixed(1)}%
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <p className="text-slate-700 text-base font-medium mb-2">Spec Disadvantages</p>
        <p className="text-orange-400 text-3xl font-bold">{summary.spec_disadvantages.count}</p>
        <p className="text-orange-400 text-base font-medium">
          {summary.spec_disadvantages.percentage_change.toFixed(1)}%
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <p className="text-slate-700 text-base font-medium mb-2">Price Increases</p>
        <p className="text-green-500 text-3xl font-bold">{summary.price_increases.count}</p>
        <p className="text-green-500 text-base font-medium">
          +{summary.price_increases.percentage_change.toFixed(1)}%
        </p>
      </div>
    </div>
  )
}

