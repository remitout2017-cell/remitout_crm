import { baseApi } from '../../store/baseApi'
import type { Lead, LeadInput } from '../../types'

export const leadsApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getLeads: b.query<Lead[], void>({ query: () => '/leads?limit=200', providesTags: ['Lead'] }),
    getLead: b.query<Lead, number>({ query: (id) => `/leads/${id}`, providesTags: (_r, _e, id) => [{ type: 'Lead', id }] }),
    addLead: b.mutation<Lead, LeadInput>({
      query: (body) => ({ url: '/leads', method: 'POST', body }),
      invalidatesTags: ['Lead'],
    }),
  }),
})

export const { useGetLeadsQuery, useGetLeadQuery, useAddLeadMutation } = leadsApi
