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
  primary: 'bg-brand-500 text-white hover:bg-brand-600 shadow-lg shadow-brand-500/30',
  secondary: 'border border-white/60 bg-white/40 text-ink backdrop-blur-md hover:bg-white/60',
  ghost: 'text-muted hover:bg-white/40',
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
