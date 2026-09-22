import { motion } from 'framer-motion'

export interface Column<T> { header: string; cell: (row: T) => React.ReactNode }
interface Props<T> {
  columns: Column<T>[]
  rows?: T[] | null
  loading?: boolean
  rowKey: (row: T) => string | number
  onRowClick?: (row: T) => void
  empty?: string
}

export function DataTable<T>({ columns, rows, loading, rowKey, onRowClick, empty = 'Nothing here yet.' }: Props<T>) {
  return (
    <div className="glass overflow-x-auto rounded-2xl">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-white/50 bg-white/20 text-xs uppercase tracking-wide text-muted">
          <tr>{columns.map((c) => <th key={c.header} className="px-4 py-3 font-semibold">{c.header}</th>)}</tr>
        </thead>
        <tbody>
          {loading && Array.from({ length: 4 }, (_, i) => (
            <tr key={i}><td colSpan={columns.length} className="px-4 py-3"><div className="h-4 animate-pulse rounded bg-white/40" /></td></tr>
          ))}
          {!loading && rows?.length === 0 && (
            <tr><td colSpan={columns.length} className="px-4 py-10 text-center text-muted">{empty}</td></tr>
          )}
          {!loading && rows?.map((r, i) => (
            <motion.tr
              key={rowKey(r)}
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
              onClick={() => onRowClick?.(r)}
              className={`border-t border-white/30 ${onRowClick ? 'cursor-pointer hover:bg-white/30' : ''}`}
            >
              {columns.map((c) => <td key={c.header} className="px-4 py-3">{c.cell(r)}</td>)}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
