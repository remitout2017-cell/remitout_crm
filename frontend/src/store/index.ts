import { configureStore } from '@reduxjs/toolkit'
import { useDispatch, useSelector } from 'react-redux'
import onboarding from '../features/partners/slice'
import { baseApi } from './baseApi'

export const store = configureStore({
  reducer: { [baseApi.reducerPath]: baseApi.reducer, onboarding },
  middleware: (gdm) => gdm().concat(baseApi.middleware),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
export const useAppDispatch = useDispatch.withTypes<AppDispatch>()
export const useAppSelector = useSelector.withTypes<RootState>()
