import { FiCheck } from 'react-icons/fi'
import { cn } from '../../utils/cn'

/** Horizontal progress indicator; `current` is the 1-based active step. */
export function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <ol className="flex items-center gap-2">
      {steps.map((s, i) => {
        const done = i + 1 < current
        const active = i + 1 === current
        return (
          <li key={s} className="flex flex-1 items-center gap-2">
            <span className={cn('grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-bold',
              done ? 'bg-brand-500 text-white' : active ? 'border-2 border-brand-500 text-brand-600' : 'bg-brand-100 text-muted')}>
              {done ? <FiCheck /> : i + 1}
            </span>
            <span className={cn('hidden text-xs font-medium sm:block', active ? 'text-ink' : 'text-muted')}>{s}</span>
            {i < steps.length - 1 && <span className={cn('h-0.5 flex-1', done ? 'bg-brand-500' : 'bg-brand-200')} />}
          </li>
        )
      })}
    </ol>
  )
}
