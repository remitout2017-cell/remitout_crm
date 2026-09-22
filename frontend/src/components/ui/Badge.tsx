import { cn } from '../../utils/cn'

const tones = {
  brand: 'bg-brand-200 text-brand-700',
  green: 'bg-green-100 text-green-700',
  red: 'bg-red-100 text-red-700',
  gray: 'bg-gray-100 text-gray-600',
}
export type Tone = keyof typeof tones

export function Badge({ tone = 'gray', children }: { tone?: Tone; children: React.ReactNode }) {
  return (
    <span className={cn('inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize', tones[tone])}>
      {children}
    </span>
  )
}
