import { FiUploadCloud } from 'react-icons/fi'
import { cn } from '../../utils/cn'

interface Props { label: string; file: File | null; onChange: (f: File | null) => void; accept?: string; required?: boolean; className?: string }

export function FileField({ label, file, onChange, accept = '.pdf,.png,.jpg,.jpeg', required, className }: Props) {
  return (
    <label className={cn('block text-sm', className)}>
      <span className="mb-1 block font-medium text-muted">{label}</span>
      <span className="flex items-center gap-2 rounded-lg border border-dashed border-white/70 bg-white/30 px-3 py-2 text-sm text-muted backdrop-blur-md transition-colors hover:bg-white/45">
        <FiUploadCloud className="shrink-0" />
        <span className="truncate">{file ? file.name : 'Choose a file…'}</span>
        <input
          type="file"
          accept={accept}
          required={required && !file}
          className="hidden"
          onChange={(e) => onChange(e.target.files?.[0] ?? null)}
        />
      </span>
    </label>
  )
}
