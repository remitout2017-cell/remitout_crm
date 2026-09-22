import { baseApi } from '../../store/baseApi'
import type { FormReferenceData } from '../../types'

/** Edubao's form-required-data (app types, titles, document types), cached per partner account. */
export const referenceApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getFormData: b.query<FormReferenceData, number>({
      query: (partnerAccountId) => `/reference/form-data?partner_account_id=${partnerAccountId}`,
    }),
  }),
})

export const { useGetFormDataQuery } = referenceApi
