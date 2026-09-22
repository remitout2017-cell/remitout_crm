import { cn } from '../../utils/cn'

const tones = {
  brand: 'bg-brand-500/15 text-brand-700 ring-1 ring-brand-500/20',
  green: 'bg-emerald-500/15 text-emerald-700 ring-1 ring-emerald-500/20',
  red: 'bg-red-500/15 text-red-700 ring-1 ring-red-500/20',
  gray: 'bg-white/40 text-muted ring-1 ring-white/50',
}
export type Tone = keyof typeof tones

export function Badge({ tone = 'gray', children }: { tone?: Tone; children: React.ReactNode }) {
  return (
    <span className={cn('inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize backdrop-blur-sm', tones[tone])}>
      {children}
    </span>
  )
}
