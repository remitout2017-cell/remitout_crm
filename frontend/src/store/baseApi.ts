import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Backend has no CORS, so dev traffic goes through the Vite `/api` proxy.
// Each feature adds its own endpoints with `baseApi.injectEndpoints`.
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (h) => {
      h.set('X-Admin-Key', import.meta.env.VITE_ADMIN_KEY ?? '')
      return h
    },
  }),
  tagTypes: ['Student', 'Lead', 'Partner'],
  endpoints: () => ({}),
})

/** Pulls the backend's `detail` message out of an RTK Query error. */
export const errorMessage = (e: unknown): string => {
  const d = (e as { data?: { detail?: unknown } })?.data?.detail
  return typeof d === 'string' ? d : 'Something went wrong'
}
