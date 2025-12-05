export type FieldType = 'text' | 'integer' | 'decimal' | 'boolean'
export type CompareDirection = 'lower' | 'higher'

export interface FieldDefinition {
  name: string
  type: FieldType
  unit?: string
  label: string
  compareDirection: CompareDirection
  required: boolean
}

export interface MetricDefinition {
  name: string
  formula: string
  label: string
  compareDirection: CompareDirection
  format?: string
}

export interface ProductSchema {
  fields: FieldDefinition[]
  metrics?: MetricDefinition[]
}

export interface Product {
  id: string
  sku?: string
  name: string
  product_type: string
  schema: ProductSchema
  data: Record<string, any>
  user_id: string
  created_at: string
  updated_at: string
}

export interface CompetitorListing {
  id: string
  my_product_id: string
  url: string
  retailer_name: string
  product_name: string
  data: Record<string, any>
  last_crawled_at?: string
  created_at: string
}

export interface ProductTemplate {
  id: string
  name: string
  schema: ProductSchema
  is_system: boolean
  user_id?: string
  created_at: string
}

