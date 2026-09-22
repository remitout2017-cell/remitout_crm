import type { IconType } from 'react-icons'
import { LuBriefcase, LuFileText, LuLayoutDashboard, LuUsers } from 'react-icons/lu'

export interface NavItem { label: string; href: string; icon: IconType }

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/', icon: LuLayoutDashboard },
  { label: 'Students', href: '/students', icon: LuUsers },
  { label: 'Leads', href: '/leads', icon: LuFileText },
  { label: 'Partners', href: '/partners', icon: LuBriefcase },
]

export const isActivePath = (pathname: string, href: string) =>
  href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(href + '/')

export const activeLabel = (pathname: string) =>
  NAV_ITEMS.find((i) => isActivePath(pathname, i.href))?.label ?? 'Menu'
