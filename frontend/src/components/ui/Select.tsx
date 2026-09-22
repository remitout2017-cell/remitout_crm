import { cn } from '../../utils/cn'

interface Props extends React.SelectHTMLAttributes<HTMLSelectElement> { label?: string }

export function Select({ label, className, children, ...rest }: Props) {
  return (
    <label className="block text-sm">
      {label && <span className="mb-1 block font-medium text-muted">{label}</span>}
      <select
        className={cn('w-full rounded-lg border border-brand-200 bg-white px-3 py-2 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20', className)}
        {...rest}
      >
        {children}
      </select>
    </label>
  )
}
