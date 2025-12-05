import { useState } from 'react'
import api from '../../lib/api'
import { ProductSchema, FieldDefinition, MetricDefinition } from '../../types/schema'

interface AddProductModalProps {
  onClose: () => void
  onSuccess: () => void
}

export default function AddProductModal({ onClose, onSuccess }: AddProductModalProps) {
  const [step, setStep] = useState(1)
  const [name, setName] = useState('')
  const [sku, setSku] = useState('')
  const [productType, setProductType] = useState('custom')
  const [schema, setSchema] = useState<ProductSchema>({
    fields: [],
    metrics: []
  })
  const [data, setData] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(false)

  const addField = () => {
    setSchema({
      ...schema,
      fields: [
        ...schema.fields,
        {
          name: '',
          type: 'text',
          label: '',
          compareDirection: 'lower',
          required: true
        }
      ]
    })
  }

  const updateField = (index: number, field: Partial<FieldDefinition>) => {
    const newFields = [...schema.fields]
    newFields[index] = { ...newFields[index], ...field }
    setSchema({ ...schema, fields: newFields })
  }

  const removeField = (index: number) => {
    setSchema({
      ...schema,
      fields: schema.fields.filter((_, i) => i !== index)
    })
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      await api.post('/products', {
        name,
        sku: sku || undefined,
        product_type: productType,
        schema,
        data
      })
      onSuccess()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create product')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl m-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900">New Product Entry</h2>
        </div>

        <div className="p-6">
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Product Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">SKU</label>
                <input
                  type="text"
                  value={sku}
                  onChange={(e) => setSku(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Product Type
                </label>
                <input
                  type="text"
                  value={productType}
                  onChange={(e) => setProductType(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <button
                onClick={() => setStep(2)}
                className="w-full bg-primary text-white py-2 px-4 rounded-lg font-semibold hover:bg-primary/90"
              >
                Next: Define Schema
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold">Fields</h3>
                <button
                  onClick={addField}
                  className="text-sm text-primary hover:underline"
                >
                  + Add Field
                </button>
              </div>

              {schema.fields.map((field, index) => (
                <div key={index} className="border border-slate-200 rounded-lg p-4 space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      placeholder="Field name"
                      value={field.name}
                      onChange={(e) => updateField(index, { name: e.target.value })}
                      className="px-2 py-1 border border-slate-300 rounded text-sm"
                    />
                    <input
                      placeholder="Label"
                      value={field.label}
                      onChange={(e) => updateField(index, { label: e.target.value })}
                      className="px-2 py-1 border border-slate-300 rounded text-sm"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <select
                      value={field.type}
                      onChange={(e) => updateField(index, { type: e.target.value as any })}
                      className="px-2 py-1 border border-slate-300 rounded text-sm"
                    >
                      <option value="text">Text</option>
                      <option value="integer">Integer</option>
                      <option value="decimal">Decimal</option>
                      <option value="boolean">Boolean</option>
                    </select>
                    <select
                      value={field.compareDirection}
                      onChange={(e) => updateField(index, { compareDirection: e.target.value as any })}
                      className="px-2 py-1 border border-slate-300 rounded text-sm"
                    >
                      <option value="lower">Lower is better</option>
                      <option value="higher">Higher is better</option>
                    </select>
                    <button
                      onClick={() => removeField(index)}
                      className="text-red-500 text-sm hover:underline"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}

              <div className="flex gap-2">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 bg-slate-200 text-slate-700 py-2 px-4 rounded-lg font-semibold hover:bg-slate-300"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 bg-primary text-white py-2 px-4 rounded-lg font-semibold hover:bg-primary/90"
                >
                  Next: Enter Data
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="font-semibold">Product Data</h3>
              {schema.fields.map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {field.label} {field.required && '*'}
                  </label>
                  <input
                    type={field.type === 'integer' || field.type === 'decimal' ? 'number' : 'text'}
                    value={data[field.name] || ''}
                    onChange={(e) => {
                      const value = field.type === 'integer' 
                        ? parseInt(e.target.value, 10)
                        : field.type === 'decimal'
                        ? parseFloat(e.target.value)
                        : e.target.value
                      setData({ ...data, [field.name]: value })
                    }}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    required={field.required}
                  />
                </div>
              ))}

              <div className="flex gap-2">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 bg-slate-200 text-slate-700 py-2 px-4 rounded-lg font-semibold hover:bg-slate-300"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : 'Save Product'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="text-sm font-semibold text-slate-700 hover:text-slate-900"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

