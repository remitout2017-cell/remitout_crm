import { baseApi } from '../../store/baseApi'
import type { FormReferenceData } from '../../types'

export interface Country { name: string; iso3: string }
export interface DocTypeOption { value: string; label: string }

// Edubao's doc-type entries look like: { id: 19, doc_type_id: 14, doc_title: "Visa Application", doc_key: "visa_application_for_chance_card", size_limit: {...} }.
// The id (not doc_type_id) is what's submitted as visa_eligibility_doc_type.
function looksLikeDocType(item: unknown): item is Record<string, unknown> {
  return !!item && typeof item === 'object' && ('doc_title' in item || 'doc_key' in item || 'doc_type_id' in item)
}

function toOption(item: unknown): DocTypeOption | null {
  if (typeof item === 'string' || typeof item === 'number') return { value: String(item), label: String(item) }
  if (item && typeof item === 'object') {
    const o = item as Record<string, unknown>
    const value = o.id ?? o.code ?? o.value ?? o.key ?? o.doc_type_id
    const label = o.doc_title ?? o.label ?? o.name ?? o.title ?? o.description ?? value
    if (value != null) return { value: String(value), label: String(label) }
  }
  return null
}

/** Finds the array of doc-type-shaped objects anywhere in the response, wherever its container key is named. */
function findDocTypeArray(obj: Record<string, unknown>, depth = 0): unknown[] | null {
  if (depth > 4) return null
  for (const v of Object.values(obj)) {
    if (Array.isArray(v) && v.some(looksLikeDocType)) return v
  }
  for (const v of Object.values(obj)) {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      const nested = findDocTypeArray(v as Record<string, unknown>, depth + 1)
      if (nested) return nested
    }
  }
  return null
}

/** Fallback: any array whose container key mentions "doc", for shapes that don't match the known doc-type fields. */
function findArrayByKeyName(obj: Record<string, unknown>, keyPattern: RegExp, depth = 0): unknown[] | null {
  if (depth > 3) return null
  for (const [k, v] of Object.entries(obj)) {
    if (Array.isArray(v) && keyPattern.test(k)) return v
  }
  for (const v of Object.values(obj)) {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      const nested = findArrayByKeyName(v as Record<string, unknown>, keyPattern, depth + 1)
      if (nested) return nested
    }
  }
  return null
}

/** Edubao's form-required-data shape isn't fixed (see `FormReferenceData`); best-effort pull the document-type list out of it. */
export function extractDocTypes(data: FormReferenceData | undefined): DocTypeOption[] {
  if (!data) return []
  const found = findDocTypeArray(data) ?? findArrayByKeyName(data, /doc/i)
  if (!found) return []
  return found.map(toOption).filter((o): o is DocTypeOption => o !== null)
}

/** Same "docs" list as `extractDocTypes`, but keyed by the string `doc_key` (e.g. "passport") used when uploading a document. */
export function extractDocKeys(data: FormReferenceData | undefined): DocTypeOption[] {
  if (!data) return []
  const found = findDocTypeArray(data) ?? findArrayByKeyName(data, /doc/i)
  if (!found) return []
  return found
    .map((item): DocTypeOption | null => {
      if (!item || typeof item !== 'object' || !('doc_key' in item)) return null
      const o = item as Record<string, unknown>
      return typeof o.doc_key === 'string' ? { value: o.doc_key, label: String(o.doc_title ?? o.doc_key) } : null
    })
    .filter((o): o is DocTypeOption => o !== null)
}

/** Edubao's form-required-data (app types, titles, document types), cached per partner account. */
export const referenceApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getFormData: b.query<FormReferenceData, number>({
      query: (partnerAccountId) => `/reference/form-data?partner_account_id=${partnerAccountId}`,
    }),
    getCountries: b.query<Country[], string>({
      query: (q) => `/reference/countries?q=${encodeURIComponent(q)}&limit=20`,
    }),
  }),
})

export const { useGetFormDataQuery, useGetCountriesQuery } = referenceApi
