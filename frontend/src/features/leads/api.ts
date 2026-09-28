import { baseApi } from '../../store/baseApi'
import type { Lead, LeadInput, LeadUpdate, Step2Input, Step3Input, Step4Input } from '../../types'

export const leadsApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getLeads: b.query<Lead[], void>({ query: () => '/leads?limit=200', providesTags: ['Lead'] }),
    getLead: b.query<Lead, number>({ query: (id) => `/leads/${id}`, providesTags: (_r, _e, id) => [{ type: 'Lead', id }] }),
    addLead: b.mutation<Lead, LeadInput>({
      query: (body) => ({ url: '/leads', method: 'POST', body }),
      invalidatesTags: ['Lead'],
    }),
    updateLead: b.mutation<Lead, { id: number; body: LeadUpdate }>({
      query: ({ id, body }) => ({ url: `/leads/${id}`, method: 'PATCH', body }),
      invalidatesTags: (_r, _e, { id }) => [{ type: 'Lead', id }, 'Lead'],
    }),
    deleteLead: b.mutation<void, number>({
      query: (id) => ({ url: `/leads/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Lead'],
    }),
    submitStep2: b.mutation<Lead, { leadId: number; body: Step2Input }>({
      query: ({ leadId, body }) => ({ url: `/leads/${leadId}/steps/2`, method: 'PUT', body }),
      invalidatesTags: (_r, _e, { leadId }) => [{ type: 'Lead', id: leadId }, 'Lead'],
    }),
    submitStep3: b.mutation<Lead, { leadId: number; body: Step3Input }>({
      query: ({ leadId, body }) => ({ url: `/leads/${leadId}/steps/3`, method: 'PUT', body }),
      invalidatesTags: (_r, _e, { leadId }) => [{ type: 'Lead', id: leadId }, 'Lead'],
    }),
    submitStep4: b.mutation<Lead, { leadId: number; body: Step4Input }>({
      query: ({ leadId, body }) => ({ url: `/leads/${leadId}/steps/4`, method: 'PUT', body }),
      invalidatesTags: (_r, _e, { leadId }) => [{ type: 'Lead', id: leadId }, 'Lead'],
    }),
  }),
})

export const {
  useGetLeadsQuery, useGetLeadQuery, useAddLeadMutation, useUpdateLeadMutation, useDeleteLeadMutation,
  useSubmitStep2Mutation, useSubmitStep3Mutation, useSubmitStep4Mutation,
} = leadsApi
