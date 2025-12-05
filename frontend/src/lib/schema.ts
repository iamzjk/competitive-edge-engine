import { ProductSchema, FieldDefinition } from '../types/schema'

/**
 * Validate schema structure
 */
export function validateSchema(schema: ProductSchema): { valid: boolean; errors: string[] } {
  const errors: string[] = []
  
  // Check for duplicate field names
  const fieldNames = schema.fields.map(f => f.name)
  if (fieldNames.length !== new Set(fieldNames).size) {
    errors.push('Duplicate field names found')
  }
  
  // Validate each field
  schema.fields.forEach((field, index) => {
    if (!field.name) {
      errors.push(`Field ${index + 1}: name is required`)
    }
    if (!field.label) {
      errors.push(`Field ${index + 1}: label is required`)
    }
  })
  
  // Check for duplicate metric names
  if (schema.metrics) {
    const metricNames = schema.metrics.map(m => m.name)
    if (metricNames.length !== new Set(metricNames).size) {
      errors.push('Duplicate metric names found')
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  }
}

/**
 * Validate data against schema
 */
export function validateData(data: Record<string, any>, schema: ProductSchema): { valid: boolean; errors: string[] } {
  const errors: string[] = []
  
  // Check required fields
  schema.fields.forEach(field => {
    if (field.required && !(field.name in data)) {
      errors.push(`Required field '${field.name}' is missing`)
    }
  })
  
  // Validate field types
  schema.fields.forEach(field => {
    if (field.name in data) {
      const value = data[field.name]
      
      if (field.type === 'integer' && !Number.isInteger(value)) {
        errors.push(`Field '${field.name}' must be an integer`)
      } else if (field.type === 'decimal' && typeof value !== 'number') {
        errors.push(`Field '${field.name}' must be a decimal number`)
      } else if (field.type === 'boolean' && typeof value !== 'boolean') {
        errors.push(`Field '${field.name}' must be a boolean`)
      } else if (field.type === 'text' && typeof value !== 'string') {
        errors.push(`Field '${field.name}' must be a string`)
      }
    }
  })
  
  return {
    valid: errors.length === 0,
    errors
  }
}

/**
 * Normalize data types according to schema
 */
export function normalizeData(data: Record<string, any>, schema: ProductSchema): Record<string, any> {
  const normalized: Record<string, any> = {}
  
  schema.fields.forEach(field => {
    if (field.name in data) {
      const value = data[field.name]
      
      try {
        if (field.type === 'integer') {
          normalized[field.name] = parseInt(value, 10)
        } else if (field.type === 'decimal') {
          normalized[field.name] = parseFloat(value)
        } else if (field.type === 'boolean') {
          normalized[field.name] = Boolean(value)
        } else if (field.type === 'text') {
          normalized[field.name] = String(value)
        }
      } catch {
        normalized[field.name] = value
      }
    }
  })
  
  return normalized
}

