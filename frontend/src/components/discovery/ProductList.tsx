import { Product } from '../../types/schema'

interface ProductListProps {
  products: Product[]
  selectedProduct: Product | null
  onSelectProduct: (product: Product) => void
  onAddProduct: () => void
  loading: boolean
}

export default function ProductList({
  products,
  selectedProduct,
  onSelectProduct,
  onAddProduct,
  loading
}: ProductListProps) {
  return (
    <aside className="w-96 border-r border-slate-200 bg-white flex flex-col">
      <div className="p-4 border-b border-slate-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-slate-900">My Products</h2>
          <button
            onClick={onAddProduct}
            className="flex items-center gap-2 bg-primary text-white text-sm font-semibold py-2 px-3 rounded-lg hover:bg-primary/90"
          >
            <span className="material-symbols-outlined text-xl">add</span>
            <span>New</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="text-center py-8 text-slate-500">Loading...</div>
        ) : products.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            No products yet. Click "New" to add one.
          </div>
        ) : (
          <div className="space-y-1">
            {products.map((product) => (
              <div
                key={product.id}
                onClick={() => onSelectProduct(product)}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedProduct?.id === product.id
                    ? 'bg-slate-100'
                    : 'hover:bg-slate-50'
                }`}
              >
                <p className="text-sm font-medium text-slate-800">{product.name}</p>
                {product.sku && (
                  <p className="text-xs text-slate-500 mt-1">SKU: {product.sku}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}

