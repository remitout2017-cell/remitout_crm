import { baseApi } from '../../store/baseApi'
import type { Partner, PartnerStart } from '../../types'

export const partnersApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    startOnboarding: b.mutation<Partner, PartnerStart>({
      query: (body) => ({ url: '/partners/onboard/start', method: 'POST', body }),
    }),
    verifyOnboarding: b.mutation<Partner, { id: number; otp: string }>({
      query: ({ id, otp }) => ({ url: `/partners/onboard/${id}/verify-otp`, method: 'POST', body: { otp } }),
    }),
  }),
})

export const { useStartOnboardingMutation, useVerifyOnboardingMutation } = partnersApi
