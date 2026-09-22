export const cn = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(' ')

export const fmtDate = (d?: string | null) =>
  d ? new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : '—'
