import { motion } from 'framer-motion'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'

/** Shared shell: soft gradient backdrop with blurred orbs, icon-rail sidebar, scrolling content. */
export function AppLayout() {
  const { pathname } = useLocation()
  return (
    <div className="relative flex h-dvh w-full flex-col overflow-hidden bg-gradient-to-br from-white via-orange-50/60 to-orange-100/40 p-2 sm:p-4 md:flex-row md:gap-4">
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-20 left-1/3 h-96 w-96 rounded-full bg-orange-300/60 blur-3xl" />
        <div className="absolute bottom-0 right-10 h-80 w-80 rounded-full bg-amber-200/60 blur-3xl" />
        <div className="absolute right-1/3 top-1/3 h-72 w-72 rounded-full bg-rose-200/50 blur-3xl" />
        <div className="absolute left-10 top-1/2 h-64 w-64 rounded-full bg-sky-200/40 blur-3xl" />
      </div>
      <Sidebar />
      <main className="relative z-10 min-w-0 flex-1 overflow-y-auto overflow-x-hidden px-3 py-2 sm:px-6">
        <motion.div key={pathname} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
