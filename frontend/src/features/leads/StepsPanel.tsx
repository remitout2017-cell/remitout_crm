import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { FiLock } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { Autocomplete } from '../../components/ui/Autocomplete'
import { errorMessage } from '../../store/baseApi'
import { emptyPlace, type Lead, type Step2Input, type Step3Input } from '../../types'
import { useSubmitStep2Mutation, useSubmitStep3Mutation, useSubmitStep4Mutation } from './api'
import { PlaceFields } from './PlaceFields'
import { extractDocTypes, useGetCountriesQuery, useGetFormDataQuery } from '../reference/api'
import { useGetStudentQuery } from '../students/api'

const toTitleCase = (v: string) => v.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase())

const emptyStep2: Step2Input = {
  diff_maiden_name: '', nationality: '', nationality_iso: '', date_of_birth: '',
  place_of_birth: emptyPlace, passport_num: '', passport_issued_date: '', passport_valid_upto: '',
  passport_issue_place: emptyPlace,
}
const emptyStep3: Step3Input = { blocked_acc_amt: '', blocked_acc_duration: '', visa_eligibility_doc_type: '' }
const ISO_PATTERN = /^[A-Z]{3}$/
const isoError = (v: string) => v !== '' && !ISO_PATTERN.test(v) ? 'Must be 3 letters, e.g. IND (ISO alpha-3 code)' : undefined
const isValidPlace = (p: Step2Input['place_of_birth']) =>
  p.location !== '' && p.city !== '' && p.state !== '' && p.country !== '' && ISO_PATTERN.test(p.iso)

function StepShell({ step, title, state, editing, canEdit, onToggleEdit, children }: {
  step: number; title: string; state: 'done' | 'active' | 'locked'
  editing?: boolean; canEdit?: boolean; onToggleEdit?: () => void; children?: React.ReactNode
}) {
  return (
    <Card
      className={state === 'locked' ? 'opacity-60' : undefined}
      title={`Step ${step} · ${title}`}
      action={
        state === 'done' ? (
          <div className="flex items-center gap-2">
            <Badge tone="green">Completed</Badge>
            {canEdit && <Button variant="secondary" onClick={onToggleEdit}>{editing ? 'Cancel' : 'Edit'}</Button>}
          </div>
        )
        : state === 'locked' ? <Badge tone="gray"><FiLock className="inline -mt-0.5" /> Locked</Badge>
        : <Badge tone="brand">In progress</Badge>
      }
    >
      {state === 'locked' ? <p className="text-sm text-muted">Complete the previous step first.</p>
       : state === 'done' && !editing ? <p className="text-sm text-muted">Submitted to Edubao.</p>
       : children}
    </Card>
  )
}

function Step2Form({ lead, prefill, onSaved }: { lead: Lead; prefill?: boolean; onSaved?: () => void }) {
  const [f, setF] = useState(emptyStep2)
  const [submit, { isLoading }] = useSubmitStep2Mutation()
  const { data: student } = useGetStudentQuery(lead.student_id, { skip: !prefill })

  useEffect(() => {
    if (!student) return
    setF({
      diff_maiden_name: student.diff_maiden_name ?? '',
      nationality: student.nationality ?? '',
      nationality_iso: student.nationality_iso ?? '',
      date_of_birth: student.date_of_birth ?? '',
      place_of_birth: student.birth_place ?? emptyPlace,
      passport_num: student.passport_num ?? '',
      passport_issued_date: student.passport_issued_date ?? '',
      passport_valid_upto: student.passport_valid_upto ?? '',
      passport_issue_place: student.passport_issue_place ?? emptyPlace,
    })
  }, [student])

  const nationalityIsoError = isoError(f.nationality_iso)
  const canSubmit = f.nationality !== '' && !nationalityIsoError
    && isValidPlace(f.place_of_birth) && isValidPlace(f.passport_issue_place)

  // Nationality is a country name too, so it gets the same backend-searched dropdown as Place Country fields.
  const [nationalityQuery, setNationalityQuery] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setNationalityQuery(f.nationality.trim()), 200)
    return () => clearTimeout(t)
  }, [f.nationality])
  const { data: nationalityMatches } = useGetCountriesQuery(nationalityQuery, { skip: nationalityQuery === '' })
  const nationalityOptions = (nationalityMatches ?? []).map((c) => c.name)
  const pickNationality = (name: string) => {
    const match = nationalityMatches?.find((c) => c.name === name)
    setF({ ...f, nationality: toTitleCase(name), nationality_iso: match ? match.iso3 : f.nationality_iso })
  }

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    try {
      await submit({ leadId: lead.id, body: f }).unwrap()
      toast.success('Step 2 submitted')
      onSaved?.()
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <form onSubmit={submitForm} className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Different maiden name" placeholder="e.g. Smith (if applicable)" value={f.diff_maiden_name} onChange={(e) => setF({ ...f, diff_maiden_name: e.target.value })} />
        <Input label="Date of birth" type="date" required value={f.date_of_birth} onChange={(e) => setF({ ...f, date_of_birth: e.target.value })} />
        <Autocomplete label="Nationality" placeholder="India" value={f.nationality} options={nationalityOptions} onChange={pickNationality} />
        <Input label="Nationality ISO" placeholder="IND" required maxLength={3} pattern="[A-Z]{3}" title="3-letter ISO alpha-3 code, e.g. IND"
          error={nationalityIsoError} value={f.nationality_iso}
          onChange={(e) => setF({ ...f, nationality_iso: e.target.value.toUpperCase().replace(/[^A-Z]/g, '') })} />
      </div>
      <PlaceFields label="Place of birth" value={f.place_of_birth} onChange={(p) => setF({ ...f, place_of_birth: p })} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Passport number" placeholder="e.g. A1234567" required value={f.passport_num} onChange={(e) => setF({ ...f, passport_num: e.target.value })} />
        <div />
        <Input label="Passport issued date" type="date" required value={f.passport_issued_date} onChange={(e) => setF({ ...f, passport_issued_date: e.target.value })} />
        <Input label="Passport valid upto" type="date" required value={f.passport_valid_upto} onChange={(e) => setF({ ...f, passport_valid_upto: e.target.value })} />
      </div>
      <PlaceFields label="Passport issue place" value={f.passport_issue_place} onChange={(p) => setF({ ...f, passport_issue_place: p })} />
      <div className="flex justify-end"><Button type="submit" loading={isLoading} disabled={!canSubmit}>Submit step 2</Button></div>
    </form>
  )
}

function Step3Form({ lead, prefill, onSaved }: { lead: Lead; prefill?: boolean; onSaved?: () => void }) {
  const [f, setF] = useState(emptyStep3)
  const [submit, { isLoading }] = useSubmitStep3Mutation()
  const formData = useGetFormDataQuery(lead.partner_account_id)
  const docTypes = extractDocTypes(formData.data)

  useEffect(() => {
    if (!prefill) return
    setF({
      blocked_acc_amt: lead.blocked_acc_amt ?? '',
      blocked_acc_duration: lead.blocked_acc_duration != null ? String(lead.blocked_acc_duration) : '',
      visa_eligibility_doc_type: lead.visa_eligibility_doc_type ?? '',
    })
  }, [prefill, lead])

  const amount = Number(f.blocked_acc_amt)
  const amountError = f.blocked_acc_amt !== '' && !(amount > 0) ? 'Must be greater than 0' : undefined
  const duration = Number(f.blocked_acc_duration)
  const durationError = f.blocked_acc_duration !== '' && !(Number.isInteger(duration) && duration >= 1 && duration <= 12)
    ? 'Must be a whole number of months, 1-12' : undefined
  const canSubmit = f.blocked_acc_amt !== '' && !amountError
    && f.blocked_acc_duration !== '' && !durationError
    && f.visa_eligibility_doc_type !== ''

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    try {
      await submit({ leadId: lead.id, body: f }).unwrap()
      toast.success('Step 3 submitted')
      onSaved?.()
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <form onSubmit={submitForm} className="grid gap-3 sm:grid-cols-2">
      <Input label="Blocked account amount" type="number" step="0.01" min="0.01" placeholder="e.g. 10000" required error={amountError}
        value={f.blocked_acc_amt} onChange={(e) => setF({ ...f, blocked_acc_amt: e.target.value })} />
      <Input label="Duration (months)" type="number" min="1" max="12" placeholder="e.g. 6" required error={durationError}
        value={f.blocked_acc_duration} onChange={(e) => setF({ ...f, blocked_acc_duration: e.target.value })} />
      {docTypes.length > 0 ? (
        <Select label="Visa eligibility doc type" required className="sm:col-span-2"
          value={f.visa_eligibility_doc_type} onChange={(e) => setF({ ...f, visa_eligibility_doc_type: e.target.value })}>
          <option value="">{formData.isFetching ? 'Loading…' : 'Select…'}</option>
          {docTypes.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
        </Select>
      ) : (
        <Input label="Visa eligibility doc type" required className="sm:col-span-2"
          placeholder={formData.isFetching ? 'Loading…' : undefined}
          value={f.visa_eligibility_doc_type} onChange={(e) => setF({ ...f, visa_eligibility_doc_type: e.target.value })} />
      )}
      <p className="text-xs text-muted sm:col-span-2">Doc type code comes from Edubao's "Get Form Required Data" reference — see the Reference tab.</p>
      <div className="flex justify-end sm:col-span-2"><Button type="submit" loading={isLoading} disabled={!canSubmit}>Submit step 3</Button></div>
    </form>
  )
}

function Step4Form({ lead, prefill, onSaved }: { lead: Lead; prefill?: boolean; onSaved?: () => void }) {
  const [accepted, setAccepted] = useState(false)
  const [submit, { isLoading }] = useSubmitStep4Mutation()

  useEffect(() => { if (prefill) setAccepted(lead.terms_accepted) }, [prefill, lead])

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await submit({ leadId: lead.id, body: { terms_and_conditions: accepted } }).unwrap()
      toast.success('Application submitted')
      onSaved?.()
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <form onSubmit={submitForm} className="space-y-4">
      <label className="flex items-start gap-2 text-sm">
        <input type="checkbox" className="mt-1" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} />
        I confirm the applicant accepts Edubao's terms and conditions for the blocked account.
      </label>
      <div className="flex justify-end"><Button type="submit" loading={isLoading} disabled={!accepted}>Finalize application</Button></div>
    </form>
  )
}

/** Steps 2-4 of the blocked-account workflow; step 1 already ran when the lead was created. */
export function StepsPanel({ lead }: { lead: Lead }) {
  const next = lead.status === 'submitted' ? 5 : lead.current_step + 1
  const stateFor = (step: number): 'done' | 'active' | 'locked' =>
    lead.current_step >= step ? 'done' : step === next ? 'active' : 'locked'
  // Edubao blocks resubmitting any step once the lead's final application is submitted.
  const canEdit = lead.status !== 'submitted'
  const [editingStep, setEditingStep] = useState<number | null>(null)
  const toggle = (step: number) => setEditingStep(editingStep === step ? null : step)

  return (
    <div className="space-y-4">
      <StepShell step={2} title="Passport & identity" state={stateFor(2)}
        editing={editingStep === 2} canEdit={canEdit} onToggleEdit={() => toggle(2)}>
        {(stateFor(2) === 'active' || editingStep === 2) && (
          <Step2Form lead={lead} prefill={editingStep === 2} onSaved={editingStep === 2 ? () => setEditingStep(null) : undefined} />
        )}
      </StepShell>
      <StepShell step={3} title="Blocked account details" state={stateFor(3)}
        editing={editingStep === 3} canEdit={canEdit} onToggleEdit={() => toggle(3)}>
        {(stateFor(3) === 'active' || editingStep === 3) && (
          <Step3Form lead={lead} prefill={editingStep === 3} onSaved={editingStep === 3 ? () => setEditingStep(null) : undefined} />
        )}
      </StepShell>
      <StepShell step={4} title="Terms & submission" state={stateFor(4)}
        editing={editingStep === 4} canEdit={canEdit} onToggleEdit={() => toggle(4)}>
        {(stateFor(4) === 'active' || editingStep === 4) && (
          <Step4Form lead={lead} prefill={editingStep === 4} onSaved={editingStep === 4 ? () => setEditingStep(null) : undefined} />
        )}
      </StepShell>
    </div>
  )
}
