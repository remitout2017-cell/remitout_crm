import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { Partner } from '../../types'

interface State { partner: Partner | null }

/** Holds the in-progress Edubao partner onboarding across pages. */
const onboardingSlice = createSlice({
  name: 'onboarding',
  initialState: { partner: null } as State,
  reducers: {
    setPartner: (s, a: PayloadAction<Partner>) => { s.partner = a.payload },
    resetOnboarding: (s) => { s.partner = null },
  },
})

export const { setPartner, resetOnboarding } = onboardingSlice.actions
export default onboardingSlice.reducer
