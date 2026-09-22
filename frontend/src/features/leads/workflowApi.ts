import { baseApi } from '../../store/baseApi'
import type { LeadDocument, Payer, PayerInput, Verification } from '../../types'

/** Documents, payers & face/document verification — Edubao manual sections 4-5. */
export const leadWorkflowApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getDocuments: b.query<LeadDocument[], number>({
      query: (leadId) => `/leads/${leadId}/documents`,
      providesTags: (_r, _e, leadId) => [{ type: 'Document', id: leadId }],
    }),
    uploadDocument: b.mutation<LeadDocument, { leadId: number; docKey: string; file: File }>({
      query: ({ leadId, docKey, file }) => {
        const form = new FormData()
        form.append('doc_key', docKey)
        form.append('file', file)
        return { url: `/leads/${leadId}/documents`, method: 'POST', body: form }
      },
      invalidatesTags: (_r, _e, { leadId }) => [{ type: 'Document', id: leadId }],
    }),
    getPayers: b.query<Payer[], number>({
      query: (leadId) => `/leads/${leadId}/payers`,
      providesTags: (_r, _e, leadId) => [{ type: 'Payer', id: leadId }],
    }),
    upsertPayer: b.mutation<Payer, { leadId: number; body: PayerInput }>({
      query: ({ leadId, body }) => ({ url: `/leads/${leadId}/payers`, method: 'PUT', body }),
      invalidatesTags: (_r, _e, { leadId }) => [{ type: 'Payer', id: leadId }],
    }),
    verifyFace: b.mutation<Verification, { leadId: number; documentId: number; docType?: string; file: File }>({
      query: ({ leadId, documentId, docType, file }) => {
        const form = new FormData()
        form.append('document_id', String(documentId))
        if (docType) form.append('doc_type', docType)
        form.append('file', file)
        return { url: `/leads/${leadId}/verify/face`, method: 'POST', body: form }
      },
    }),
    verifyDocument: b.mutation<Verification, { leadId: number; documentId: number; docType?: string; file: File }>({
      query: ({ leadId, documentId, docType, file }) => {
        const form = new FormData()
        form.append('document_id', String(documentId))
        if (docType) form.append('doc_type', docType)
        form.append('file', file)
        return { url: `/leads/${leadId}/verify/document`, method: 'POST', body: form }
      },
    }),
  }),
})

export const {
  useGetDocumentsQuery, useUploadDocumentMutation,
  useGetPayersQuery, useUpsertPayerMutation,
  useVerifyFaceMutation, useVerifyDocumentMutation,
} = leadWorkflowApi
