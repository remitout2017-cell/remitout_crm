import { forwardRef } from 'react'
import { cn } from '../../utils/cn'

interface Props extends React.InputHTMLAttributes<HTMLInputElement> { label?: string; error?: string }

export const Input = forwardRef<HTMLInputElement, Props>(({ label, error, className, ...rest }, ref) => (
  <label className="block text-sm">
    {label && <span className="mb-1 block font-medium text-muted">{label}</span>}
    <input
      ref={ref}
      className={cn(
        'w-full rounded-lg border border-brand-200 bg-white px-3 py-2 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20',
        className,
      )}
      {...rest}
    />
    {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
  </label>
))
