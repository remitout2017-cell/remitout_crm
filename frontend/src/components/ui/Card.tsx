import { cn } from '../../utils/cn'

interface Props { title?: string; action?: React.ReactNode; className?: string; children: React.ReactNode }

export function Card({ title, action, className, children }: Props) {
  return (
    <section className={cn('glass rounded-2xl p-5', className)}>
      {(title || action) && (
        <header className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-bold">{title}</h3>
          {action}
        </header>
      )}
      {children}
    </section>
  )
}
