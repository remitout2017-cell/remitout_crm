import { baseApi } from '../../store/baseApi'
import type { FormLead, FormLeadPage, FormLeadPurpose } from '../../types'

export interface FormLeadSubmission {
  full_name: string
  purpose: FormLeadPurpose
  email: string
  phone_number: string
  passport_file: File
  supporting_file: File
}

export interface FormLeadQuery {
  search?: string
  page: number
  page_size: number
}

export const formLeadsApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    // Public intake — the admin key header baseApi always sends is simply ignored by this route.
    submitFormLead: b.mutation<FormLead, FormLeadSubmission>({
      query: ({ full_name, purpose, email, phone_number, passport_file, supporting_file }) => {
        const form = new FormData()
        form.append('full_name', full_name)
        form.append('purpose', purpose)
        form.append('email', email)
        form.append('phone_number', phone_number)
        form.append('passport_file', passport_file)
        form.append('supporting_file', supporting_file)
        return { url: '/form-leads', method: 'POST', body: form }
      },
      invalidatesTags: ['FormLead'],
    }),
    // Search (name/phone/email prefix) and pagination both happen server-side — the frontend only asks
    // for as many cards as fit on screen.
    getFormLeads: b.query<FormLeadPage, FormLeadQuery>({
      query: ({ search, page, page_size }) => ({ url: '/form-leads', params: { search: search || undefined, page, page_size } }),
      providesTags: ['FormLead'],
    }),
    updateFormLeadStatus: b.mutation<FormLead, { id: number; edubao_account_opened: boolean }>({
      query: ({ id, edubao_account_opened }) => ({ url: `/form-leads/${id}`, method: 'PATCH', body: { edubao_account_opened } }),
      invalidatesTags: ['FormLead'],
    }),
    deleteFormLead: b.mutation<void, number>({
      query: (id) => ({ url: `/form-leads/${id}`, method: 'DELETE' }),
      invalidatesTags: ['FormLead'],
    }),
  }),
})

export const {
  useSubmitFormLeadMutation, useGetFormLeadsQuery, useUpdateFormLeadStatusMutation, useDeleteFormLeadMutation,
} = formLeadsApi

/** Fetches a submitted document with the admin key and opens it in a new tab. */
export async function openFormLeadDocument(formLeadId: number, documentId: number, fileName: string) {
  const res = await fetch(`/api/form-leads/${formLeadId}/documents/${documentId}/file`, {
    headers: { 'X-Admin-Key': import.meta.env.VITE_ADMIN_KEY ?? '' },
  })
  if (!res.ok) throw new Error('Could not load document')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.target = '_blank'
  a.rel = 'noopener'
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 30_000)
}
