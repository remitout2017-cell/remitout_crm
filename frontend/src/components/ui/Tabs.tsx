import { motion } from 'framer-motion'
import { cn } from '../../utils/cn'

export interface TabItem { key: string; label: string }
interface Props { items: TabItem[]; active: string; onChange: (key: string) => void }

export function Tabs({ items, active, onChange }: Props) {
  return (
    <div className="glass-soft inline-flex flex-wrap gap-1 rounded-xl p-1">
      {items.map((t) => (
        <button
          key={t.key}
          type="button"
          onClick={() => onChange(t.key)}
          className={cn(
            'relative rounded-lg px-3.5 py-1.5 text-sm font-semibold transition-colors',
            active === t.key ? 'text-white' : 'text-muted hover:text-ink',
          )}
        >
          {active === t.key && (
            <motion.span layoutId="tab-pill" className="absolute inset-0 rounded-lg bg-brand-500 shadow-md shadow-brand-500/30" />
          )}
          <span className="relative">{t.label}</span>
        </button>
      ))}
    </div>
  )
}
