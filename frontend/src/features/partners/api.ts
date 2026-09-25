import { baseApi } from '../../store/baseApi'
import type { Partner, PartnerStart } from '../../types'

export const partnersApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getPartners: b.query<Partner[], void>({ query: () => '/partners', providesTags: ['Partner'] }),
    startOnboarding: b.mutation<Partner, PartnerStart>({
      query: (body) => ({ url: '/partners/onboard/start', method: 'POST', body }),
      invalidatesTags: ['Partner'],
    }),
    verifyOnboarding: b.mutation<Partner, { id: number; otp: string }>({
      query: ({ id, otp }) => ({ url: `/partners/onboard/${id}/verify-otp`, method: 'POST', body: { otp } }),
      invalidatesTags: ['Partner'],
    }),
    retryToken: b.mutation<Partner, number>({
      query: (id) => ({ url: `/partners/onboard/${id}/retry-token`, method: 'POST' }),
      invalidatesTags: ['Partner'],
    }),
  }),
})

export const { useGetPartnersQuery, useStartOnboardingMutation, useVerifyOnboardingMutation, useRetryTokenMutation } = partnersApi
