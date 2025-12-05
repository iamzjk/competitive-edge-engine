import { ProductSchema } from '../types/schema'
import { validateSchema, validateData, normalizeData } from '../lib/schema'

export function useSchema() {
  return {
    validateSchema,
    validateData,
    normalizeData
  }
}

