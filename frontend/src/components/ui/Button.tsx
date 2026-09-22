import { motion, type HTMLMotionProps } from 'framer-motion'
import { CgSpinner } from 'react-icons/cg'
import { cn } from '../../utils/cn'

type Variant = 'primary' | 'secondary' | 'ghost'
interface Props extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children?: React.ReactNode
  variant?: Variant
  loading?: boolean
  icon?: React.ReactNode
}

const styles: Record<Variant, string> = {
  primary: 'bg-brand-500 text-white hover:bg-brand-600 shadow-sm shadow-brand-500/30',
  secondary: 'bg-white text-ink border border-brand-200 hover:bg-brand-50',
  ghost: 'text-muted hover:bg-brand-200/50',
}

export function Button({ variant = 'primary', loading, icon, children, className, disabled, ...rest }: Props) {
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-60',
        styles[variant],
        className,
      )}
      {...rest}
    >
      {loading ? <CgSpinner className="animate-spin" /> : icon}
      {children}
    </motion.button>
  )
}
