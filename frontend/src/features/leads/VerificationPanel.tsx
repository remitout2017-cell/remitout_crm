import { useState } from 'react'
import toast from 'react-hot-toast'
import { FiCheckCircle } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { FileField } from '../../components/ui/FileField'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { errorMessage } from '../../store/baseApi'
import { useGetDocumentsQuery, useVerifyDocumentMutation, useVerifyFaceMutation } from './workflowApi'

function VerifyForm({ leadId, kind }: { leadId: number; kind: 'face' | 'document' }) {
  const { data: docs } = useGetDocumentsQuery(leadId)
  const [documentId, setDocumentId] = useState('')
  const [docType, setDocType] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [runFace, faceState] = useVerifyFaceMutation()
  const [runDoc, docState] = useVerifyDocumentMutation()
  const { isLoading } = kind === 'face' ? faceState : docState

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !documentId) return
    try {
      const args = { leadId, documentId: Number(documentId), docType: docType || undefined, file }
      const r = kind === 'face' ? await runFace(args).unwrap() : await runDoc(args).unwrap()
      setResult(r.result ?? 'done')
      toast.success(`${kind === 'face' ? 'Face' : 'Document'} verification complete`)
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
      <Select label="Uploaded document" required value={documentId} onChange={(e) => setDocumentId(e.target.value)}>
        <option value="">Select…</option>
        {docs?.map((d) => <option key={d.id} value={d.id}>{d.doc_key} — {d.original_file_name}</option>)}
      </Select>
      <Input label="Doc type (optional)" placeholder="passport" value={docType} onChange={(e) => setDocType(e.target.value)} />
      <FileField label={kind === 'face' ? 'Selfie' : 'Document image'} file={file} onChange={setFile} required className="sm:col-span-2" />
      <div className="flex items-center justify-between gap-3 sm:col-span-2">
        {result && <Badge tone={/match|verif/i.test(result) ? 'green' : 'brand'}><FiCheckCircle className="inline -mt-0.5" /> {result}</Badge>}
        <Button type="submit" loading={isLoading} className="ml-auto">Run {kind} verification</Button>
      </div>
    </form>
  )
}

export function VerificationPanel({ leadId }: { leadId: number }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="Face verification"><VerifyForm leadId={leadId} kind="face" /></Card>
      <Card title="Document verification"><VerifyForm leadId={leadId} kind="document" /></Card>
    </div>
  )
}
