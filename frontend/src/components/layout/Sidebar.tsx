import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { LuMenu, LuX } from 'react-icons/lu'
import { Link, useLocation } from 'react-router-dom'
import { activeLabel, isActivePath, NAV_ITEMS, type NavItem } from './nav'

type Anchor = { top: number; left: number }

/**
 * Hover tooltip for a rail icon. Portalled to <body> and `fixed` so the rail's
 * scroll container and the shell's overflow-hidden can't clip it.
 */
function useRailTooltip() {
  const [anchor, setAnchor] = useState<Anchor | null>(null)
  const show = useCallback((el: HTMLElement) => {
    const r = el.getBoundingClientRect()
    setAnchor({ top: r.top + r.height / 2, left: r.right + 12 })
  }, [])
  const hide = useCallback(() => setAnchor(null), [])
  useEffect(() => {
    if (!anchor) return
    window.addEventListener('scroll', hide, true)
    return () => window.removeEventListener('scroll', hide, true)
  }, [anchor, hide])
  const triggerProps = {
    onMouseEnter: (e: React.MouseEvent<HTMLElement>) => show(e.currentTarget),
    onMouseLeave: hide,
    onFocus: (e: React.FocusEvent<HTMLElement>) => show(e.currentTarget),
    onBlur: hide,
  }
  return { anchor, triggerProps, hide }
}

function RailTooltip({ label, anchor }: { label: string; anchor: Anchor | null }) {
  if (!anchor) return null
  return createPortal(
    <span
      role="tooltip"
      style={{ top: anchor.top, left: anchor.left }}
      className="pointer-events-none fixed z-[60] -translate-y-1/2 whitespace-nowrap rounded-full bg-brand-500 px-3 py-1 text-xs font-semibold text-white shadow-lg shadow-brand-500/30"
    >
      {label}
    </span>,
    document.body,
  )
}

function RailButton({ item, active }: { item: NavItem; active: boolean }) {
  const { anchor, triggerProps, hide } = useRailTooltip()
  const Icon = item.icon
  return (
    <>
      <Link
        to={item.href}
        aria-label={item.label}
        onClick={hide}
        {...triggerProps}
        className={`relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl transition-all duration-200 hover:scale-110 active:scale-90 ${
          active ? 'bg-white text-brand-500 shadow-md shadow-black/20' : 'text-neutral-400 hover:bg-white/10 hover:text-white'
        }`}
      >
        <Icon className="h-5 w-5" />
      </Link>
      <RailTooltip label={item.label} anchor={anchor} />
    </>
  )
}

export function Sidebar() {
  const { pathname } = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  // Lock body scroll while the drawer is open.
  useEffect(() => {
    if (!mobileOpen) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [mobileOpen])

  return (
    <>
      {/* Mobile top bar */}
      <div className="flex shrink-0 items-center justify-between rounded-3xl bg-neutral-900 px-4 py-3 shadow-xl shadow-black/20 md:hidden">
        <button type="button" onClick={() => setMobileOpen(true)} aria-label="Open menu"
          className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10 text-white">
          <LuMenu className="h-5 w-5" />
        </button>
        <span className="truncate px-2 text-sm font-semibold text-white">{activeLabel(pathname)}</span>
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-neutral-700 text-sm font-semibold text-white">R</span>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div key="backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)} className="fixed inset-0 z-40 bg-black/40 md:hidden" />
            <motion.aside key="drawer" initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 34 }}
              className="fixed inset-y-0 left-0 z-50 flex w-[82vw] max-w-xs flex-col bg-neutral-900 p-4 shadow-2xl md:hidden">
              <div className="flex items-center justify-between pb-4">
                <span className="text-base font-bold text-white">Menu</span>
                <button type="button" onClick={() => setMobileOpen(false)} aria-label="Close menu"
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white">
                  <LuX className="h-4 w-4" />
                </button>
              </div>
              <nav className="space-y-1">
                {NAV_ITEMS.map(({ label, href, icon: Icon }) => (
                  <Link key={href} to={href} onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-semibold transition-colors ${
                      isActivePath(pathname, href) ? 'bg-white text-brand-500' : 'text-neutral-300 hover:bg-white/10 hover:text-white'
                    }`}>
                    <Icon className="h-5 w-5" /> {label}
                  </Link>
                ))}
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Desktop icon rail */}
      <aside className="relative z-20 hidden w-[68px] shrink-0 flex-col items-center rounded-[2.5rem] bg-neutral-900 py-5 shadow-xl shadow-black/20 md:flex">
        <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-500 font-headings text-lg font-extrabold text-white">R</span>
        <nav className="mt-6 flex min-h-0 flex-1 flex-col items-center gap-3 overflow-y-auto">
          {NAV_ITEMS.map((item) => <RailButton key={item.href} item={item} active={isActivePath(pathname, item.href)} />)}
        </nav>
      </aside>
    </>
  )
}
