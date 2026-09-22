import { useState } from 'react'
import toast from 'react-hot-toast'
import { FiPaperclip } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { FileField } from '../../components/ui/FileField'
import { Input } from '../../components/ui/Input'
import { errorMessage } from '../../store/baseApi'
import { fmtDate } from '../../utils/cn'
import { useGetDocumentsQuery, useUploadDocumentMutation } from './workflowApi'

const fmtSize = (b: number) => (b < 1024 ? `${b} B` : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`)

export function DocumentsPanel({ leadId }: { leadId: number }) {
  const { data: docs, isLoading } = useGetDocumentsQuery(leadId)
  const [upload, { isLoading: uploading }] = useUploadDocumentMutation()
  const [docKey, setDocKey] = useState('')
  const [file, setFile] = useState<File | null>(null)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    try {
      await upload({ leadId, docKey, file }).unwrap()
      toast.success('Document uploaded')
      setDocKey(''); setFile(null)
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <div className="space-y-4">
      <Card title="Upload document">
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-[1fr_2fr_auto] sm:items-end">
          <Input label="Doc key" placeholder="passport" required pattern="[a-z0-9_]{1,50}"
            value={docKey} onChange={(e) => setDocKey(e.target.value.toLowerCase())} />
          <FileField label="File (PDF/PNG/JPEG, max 2MB)" file={file} onChange={setFile} required />
          <Button type="submit" loading={uploading} icon={<FiPaperclip />}>Upload</Button>
        </form>
      </Card>
      <Card title="Uploaded documents">
        {isLoading && <div className="h-16 animate-pulse rounded-lg bg-white/40" />}
        {!isLoading && (!docs || docs.length === 0) && <p className="text-sm text-muted">No documents uploaded yet.</p>}
        <ul className="space-y-2">
          {docs?.map((d) => (
            <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/40 bg-white/25 px-3 py-2 text-sm">
              <span className="font-semibold">{d.doc_key}</span>
              <span className="text-muted">{d.original_file_name} · {fmtSize(d.size)}</span>
              <span className="text-muted">{fmtDate(d.created_at)}</span>
              <Badge tone={d.edubao_doc_id ? 'green' : 'gray'}>{d.edubao_doc_id ? `doc #${d.edubao_doc_id}` : 'pending'}</Badge>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
