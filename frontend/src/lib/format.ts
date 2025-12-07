/**
 * Utility functions for formatting values with units
 */
import { ProductSchema, FieldDefinition } from '../types/schema'

/**
 * Format a value with its unit based on schema field definition
 */
export function formatValueWithUnit(
  value: any,
  fieldName: string,
  schema: ProductSchema
): string {
  if (value === null || value === undefined || value === '') {
    return 'N/A'
  }

  // Find field in schema
  if (!schema || !schema.fields || !Array.isArray(schema.fields)) {
    return String(value)
  }
  
  const field = schema.fields.find((f) => f.name === fieldName)
  if (!field) {
    return String(value)
  }

  // Format based on field type
  if (field.type === 'decimal') {
    const numValue = typeof value === 'number' ? value : parseFloat(value)
    if (isNaN(numValue)) {
      return String(value)
    }
    // Format decimal (remove trailing zeros)
    const formatted = numValue % 1 === 0 ? numValue.toFixed(0) : numValue.toFixed(2)
    // Always append unit if it exists and is not empty
    if (field.unit && field.unit.trim()) {
      return `${formatted} ${field.unit}`
    }
    return formatted
  }

  if (field.type === 'integer') {
    const numValue = typeof value === 'number' ? value : parseInt(value)
    if (isNaN(numValue)) {
      return String(value)
    }
    // Always append unit if it exists and is not empty
    if (field.unit && field.unit.trim()) {
      return `${numValue} ${field.unit}`
    }
    return String(numValue)
  }

  if (field.type === 'text') {
    return String(value)
  }

  if (field.type === 'boolean') {
    return value ? 'Yes' : 'No'
  }

  return String(value)
}

/**
 * Format a price value
 */
export function formatPrice(value: any): string {
  if (value === null || value === undefined || value === '') {
    return 'N/A'
  }
  const numValue = typeof value === 'number' ? value : parseFloat(value)
  if (isNaN(numValue)) {
    return 'N/A'
  }
  return `$${numValue.toFixed(2)}`
}

/**
 * Get unit for a field from schema
 */
export function getFieldUnit(fieldName: string, schema: ProductSchema): string | undefined {
  const field = schema.fields.find((f) => f.name === fieldName)
  return field?.unit
}

/**
 * Get proxied image URL to bypass CORS and referrer restrictions
 * Returns the original URL if it's empty/null, otherwise returns the proxied URL
 */
export function getProxiedImageUrl(imageUrl: string | null | undefined): string | null {
  if (!imageUrl || !imageUrl.trim()) {
    return null
  }
  
  // If it's already a data URL or relative path, return as-is
  if (imageUrl.startsWith('data:') || imageUrl.startsWith('/')) {
    return imageUrl
  }
  
  // Use the backend proxy endpoint
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  return `${API_URL}/api/v1/images/proxy?url=${encodeURIComponent(imageUrl)}`
}

