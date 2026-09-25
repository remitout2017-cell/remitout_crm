import { useEffect, useRef, useState } from 'react'
import { Input } from './Input'
import { cn } from '../../utils/cn'

interface Props {
  label: string
  value: string
  options: string[]
  onChange: (value: string) => void
  placeholder?: string
}

/** Text input with a small scrollable suggestion list right under it. Any typed value is still allowed. */
export function Autocomplete({ label, value, options, onChange, placeholder }: Props) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const box = useRef<HTMLDivElement>(null)

  const q = value.trim().toLowerCase()
  const matches = options.filter((o) => o.toLowerCase().includes(q) && o.toLowerCase() !== q)
  const shown = open && matches.length > 0

  useEffect(() => {
    const close = (e: MouseEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const pick = (v: string) => { onChange(v); setOpen(false) }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!shown) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((i) => Math.min(i + 1, matches.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((i) => Math.max(i - 1, 0)) }
    else if (e.key === 'Enter') { e.preventDefault(); pick(matches[active]) }
    else if (e.key === 'Escape') { e.stopPropagation(); setOpen(false) }
  }

  return (
    <div ref={box} className="relative">
      <Input
        label={label} value={value} placeholder={placeholder} autoComplete="off"
        onChange={(e) => { onChange(e.target.value); setOpen(true); setActive(0) }}
        onFocus={() => setOpen(true)} onKeyDown={onKeyDown}
      />
      {shown && (
        <ul role="listbox" className="absolute left-0 right-0 top-full z-30 mt-1 max-h-40 overflow-y-auto rounded-lg border border-white/10 bg-neutral-900 py-1 text-sm text-white shadow-xl [color-scheme:dark]">
          {matches.map((o, i) => (
            <li key={o} role="option" aria-selected={i === active}
              onMouseDown={(e) => { e.preventDefault(); pick(o) }} onMouseEnter={() => setActive(i)}
              className={cn('cursor-pointer px-3 py-1.5 text-white', i === active ? 'bg-brand-500' : 'hover:bg-white/10')}>
              {o}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
