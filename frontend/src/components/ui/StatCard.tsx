import { motion } from 'framer-motion'
import type { IconType } from 'react-icons'

interface Props { label: string; value: string | number; icon: IconType }

export function StatCard({ label, value, icon: Icon }: Props) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-4 rounded-xl border border-brand-200 bg-white p-5 shadow-sm"
    >
      <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand-200 text-xl text-brand-600"><Icon /></span>
      <div>
        <p className="text-sm text-muted">{label}</p>
        <p className="font-headings text-2xl font-extrabold">{value}</p>
      </div>
    </motion.div>
  )
}
