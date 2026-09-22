import { useState } from 'react'
import toast from 'react-hot-toast'
import { FiLock } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { errorMessage } from '../../store/baseApi'
import { emptyPlace, type Lead, type Step2Input, type Step3Input } from '../../types'
import { useSubmitStep2Mutation, useSubmitStep3Mutation, useSubmitStep4Mutation } from './api'
import { PlaceFields } from './PlaceFields'

const emptyStep2: Step2Input = {
  diff_maiden_name: '', nationality: '', nationality_iso: '', date_of_birth: '',
  place_of_birth: emptyPlace, passport_num: '', passport_issued_date: '', passport_valid_upto: '',
  passport_issue_place: emptyPlace,
}
const emptyStep3: Step3Input = { blocked_acc_amt: '', blocked_acc_duration: '', visa_eligibility_doc_type: '' }

function StepShell({ step, title, state, children }: { step: number; title: string; state: 'done' | 'active' | 'locked'; children?: React.ReactNode }) {
  return (
    <Card
      className={state === 'locked' ? 'opacity-60' : undefined}
      title={`Step ${step} · ${title}`}
      action={
        state === 'done' ? <Badge tone="green">Completed</Badge>
        : state === 'locked' ? <Badge tone="gray"><FiLock className="inline -mt-0.5" /> Locked</Badge>
        : <Badge tone="brand">In progress</Badge>
      }
    >
      {state === 'locked' ? <p className="text-sm text-muted">Complete the previous step first.</p>
       : state === 'done' ? <p className="text-sm text-muted">Submitted to Edubao.</p>
       : children}
    </Card>
  )
}

function Step2Form({ lead }: { lead: Lead }) {
  const [f, setF] = useState(emptyStep2)
  const [submit, { isLoading }] = useSubmitStep2Mutation()

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await submit({ leadId: lead.id, body: f }).unwrap()
      toast.success('Step 2 submitted')
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <form onSubmit={submitForm} className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Different maiden name" value={f.diff_maiden_name} onChange={(e) => setF({ ...f, diff_maiden_name: e.target.value })} />
        <Input label="Date of birth" type="date" required value={f.date_of_birth} onChange={(e) => setF({ ...f, date_of_birth: e.target.value })} />
        <Input label="Nationality" required value={f.nationality} onChange={(e) => setF({ ...f, nationality: e.target.value })} />
        <Input label="Nationality ISO" required value={f.nationality_iso} onChange={(e) => setF({ ...f, nationality_iso: e.target.value })} maxLength={3} />
      </div>
      <PlaceFields label="Place of birth" value={f.place_of_birth} onChange={(p) => setF({ ...f, place_of_birth: p })} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Passport number" required value={f.passport_num} onChange={(e) => setF({ ...f, passport_num: e.target.value })} />
        <div />
        <Input label="Passport issued date" type="date" required value={f.passport_issued_date} onChange={(e) => setF({ ...f, passport_issued_date: e.target.value })} />
        <Input label="Passport valid upto" type="date" required value={f.passport_valid_upto} onChange={(e) => setF({ ...f, passport_valid_upto: e.target.value })} />
      </div>
      <PlaceFields label="Passport issue place" value={f.passport_issue_place} onChange={(p) => setF({ ...f, passport_issue_place: p })} />
      <div className="flex justify-end"><Button type="submit" loading={isLoading}>Submit step 2</Button></div>
    </form>
  )
}

function Step3Form({ lead }: { lead: Lead }) {
  const [f, setF] = useState(emptyStep3)
  const [submit, { isLoading }] = useSubmitStep3Mutation()

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await submit({ leadId: lead.id, body: f }).unwrap()
      toast.success('Step 3 submitted')
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <form onSubmit={submitForm} className="grid gap-3 sm:grid-cols-2">
      <Input label="Blocked account amount" type="number" step="0.01" min="0.01" required
        value={f.blocked_acc_amt} onChange={(e) => setF({ ...f, blocked_acc_amt: e.target.value })} />
      <Input label="Duration (months)" type="number" min="1" required
        value={f.blocked_acc_duration} onChange={(e) => setF({ ...f, blocked_acc_duration: e.target.value })} />
      <Input label="Visa eligibility doc type" required className="sm:col-span-2"
        value={f.visa_eligibility_doc_type} onChange={(e) => setF({ ...f, visa_eligibility_doc_type: e.target.value })} />
      <p className="text-xs text-muted sm:col-span-2">Doc type code comes from Edubao's "Get Form Required Data" reference — see the Reference tab.</p>
      <div className="flex justify-end sm:col-span-2"><Button type="submit" loading={isLoading}>Submit step 3</Button></div>
    </form>
  )
}

function Step4Form({ lead }: { lead: Lead }) {
  const [accepted, setAccepted] = useState(false)
  const [submit, { isLoading }] = useSubmitStep4Mutation()

  const submitForm = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await submit({ leadId: lead.id, body: { terms_and_conditions: accepted } }).unwrap()
      toast.success('Application submitted')
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

  return (
    <div className="space-y-4">
      <StepShell step={2} title="Passport & identity" state={stateFor(2)}>{stateFor(2) === 'active' && <Step2Form lead={lead} />}</StepShell>
      <StepShell step={3} title="Blocked account details" state={stateFor(3)}>{stateFor(3) === 'active' && <Step3Form lead={lead} />}</StepShell>
      <StepShell step={4} title="Terms & submission" state={stateFor(4)}>{stateFor(4) === 'active' && <Step4Form lead={lead} />}</StepShell>
    </div>
  )
}
