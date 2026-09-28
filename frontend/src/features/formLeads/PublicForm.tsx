import { useState } from 'react'
import toast, { Toaster } from 'react-hot-toast'
import { FiCheckCircle, FiSend } from 'react-icons/fi'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { FileField } from '../../components/ui/FileField'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { errorMessage } from '../../store/baseApi'
import { PASSPORT_LABEL, PURPOSE_OPTIONS, SUPPORTING_DOC_LABELS, type FormLeadPurpose } from '../../types'
import { useSubmitFormLeadMutation } from './api'

const empty = { full_name: '', purpose: '' as FormLeadPurpose | '', email: '', phone_number: '' }

/** Dashed guide box around a field so its padding (inside the dashes) and margin (gap to the next box) are visible. */
function FieldBox({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-xl border-2 border-dashed border-orange-300/80 p-3 ${className ?? ''}`}>{children}</div>
}

export default function PublicForm() {
  const [submit, { isLoading }] = useSubmitFormLeadMutation()
  const [form, setForm] = useState(empty)
  const [passportFile, setPassportFile] = useState<File | null>(null)
  const [supportingFile, setSupportingFile] = useState<File | null>(null)
  const [done, setDone] = useState(false)

  const set = (k: keyof typeof empty) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value })

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.purpose || !passportFile || !supportingFile) return
    try {
      await submit({ ...form, purpose: form.purpose, passport_file: passportFile, supporting_file: supportingFile }).unwrap()
      setDone(true)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="relative flex min-h-dvh w-full items-center justify-center overflow-hidden bg-gradient-to-br from-white via-orange-50/60 to-orange-100/40 px-4 py-10">
      <Toaster position="top-right" />
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-20 left-1/3 h-96 w-96 rounded-full bg-orange-300/60 blur-3xl" />
        <div className="absolute bottom-0 right-10 h-80 w-80 rounded-full bg-amber-200/60 blur-3xl" />
      </div>
      <div className="relative z-10 w-full max-w-xl">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-extrabold">Upload Your Documents</h1>
          <p className="mt-1 text-sm text-muted">Tell us a bit about yourself and share your documents to get started.</p>
        </div>
        <Card className="border-2 border-dashed border-orange-300/80">
          {done ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <FiCheckCircle className="h-12 w-12 text-emerald-500" />
              <h2 className="text-lg font-bold">Thank you!</h2>
              <p className="text-sm text-muted">Your details and documents have been submitted. Our team will get in touch with you shortly.</p>
              <Button variant="secondary" onClick={() => { setForm(empty); setPassportFile(null); setSupportingFile(null); setDone(false) }}>
                Submit another response
              </Button>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="grid gap-4">
              <FieldBox>
                <Input label="Full name" required value={form.full_name} onChange={set('full_name')} placeholder="Your full name" />
              </FieldBox>
              <FieldBox>
                <Select label="Purpose" required value={form.purpose} onChange={set('purpose')}>
                  <option value="">Select purpose…</option>
                  {PURPOSE_OPTIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </Select>
              </FieldBox>
              <div className="grid gap-4 sm:grid-cols-2">
                <FieldBox>
                  <Input label="Email" type="email" required value={form.email} onChange={set('email')} placeholder="you@example.com" />
                </FieldBox>
                <FieldBox>
                  <Input label="Phone number (10 digits)" required inputMode="numeric" pattern="\d{10}" maxLength={10}
                    title="Enter exactly 10 digits, without the country code" placeholder="9876543210"
                    value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value.replace(/\D/g, '').slice(0, 10) })} />
                </FieldBox>
              </div>
              <FieldBox>
                <FileField label={`${PASSPORT_LABEL} (PDF/PNG/JPEG, max 2 MB)`} file={passportFile} onChange={setPassportFile} required />
              </FieldBox>
              {form.purpose && (
                <FieldBox>
                  <FileField
                    label={`${SUPPORTING_DOC_LABELS[form.purpose]} (PDF/PNG/JPEG, max 2 MB)`}
                    file={supportingFile}
                    onChange={setSupportingFile}
                    required
                  />
                </FieldBox>
              )}
              <Button type="submit" loading={isLoading} icon={<FiSend />} className="mt-2 w-full">
                Submit
              </Button>
            </form>
          )}
        </Card>
      </div>
    </div>
  )
}
