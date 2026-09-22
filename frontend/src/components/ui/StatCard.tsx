import { motion } from 'framer-motion'
import type { IconType } from 'react-icons'

interface Props { label: string; value: string | number; icon: IconType }

export function StatCard({ label, value, icon: Icon }: Props) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="glass flex items-center gap-4 rounded-2xl p-5"
    >
      <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand-500/15 text-xl text-brand-600 ring-1 ring-white/50"><Icon /></span>
      <div>
        <p className="text-sm text-muted">{label}</p>
        <p className="font-headings text-2xl font-extrabold">{value}</p>
      </div>
    </motion.div>
  )
}
