import { useState } from 'react'
import toast from 'react-hot-toast'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { errorMessage } from '../../store/baseApi'
import { emptyPlace, type PayerInput } from '../../types'
import { fmtDate } from '../../utils/cn'
import { PlaceFields } from './PlaceFields'
import { useGetPayersQuery, useUpsertPayerMutation } from './workflowApi'

const empty: PayerInput = {
  title: '', first_name: '', last_name: '', email: '', phone_code: '', mobile_number: '',
  date_of_birth: '', relationship: '', nationality: '', nationality_iso: '', birth_place: emptyPlace,
  street_num: '', additional_address: '', postal_code: '', city: '', state: '', country: '', country_iso: '',
  transfer_amt: '',
}

export function PayersPanel({ leadId }: { leadId: number }) {
  const { data: payers, isLoading } = useGetPayersQuery(leadId)
  const [upsert, { isLoading: saving }] = useUpsertPayerMutation()
  const [f, setF] = useState(empty)
  const set = (k: keyof PayerInput) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await upsert({ leadId, body: f }).unwrap()
      toast.success('Payer saved')
      setF(empty)
    } catch (err) { toast.error(errorMessage(err)) }
  }

  return (
    <div className="space-y-4">
      <Card title="Add / update payer">
        <form onSubmit={submit} className="space-y-4">
          <fieldset className="grid gap-3 sm:grid-cols-3">
            <Input label="Title" required value={f.title} onChange={set('title')} placeholder="Mr" />
            <Input label="First name" required value={f.first_name} onChange={set('first_name')} />
            <Input label="Last name" required value={f.last_name} onChange={set('last_name')} />
            <Input label="Email" type="email" required value={f.email} onChange={set('email')} />
            <Input label="Phone code" required value={f.phone_code} onChange={set('phone_code')} placeholder="91" />
            <Input label="Mobile number" required value={f.mobile_number} onChange={set('mobile_number')} />
            <Input label="Date of birth" type="date" required value={f.date_of_birth} onChange={set('date_of_birth')} />
            <Input label="Relationship to student" required value={f.relationship} onChange={set('relationship')} placeholder="Brother" />
            <Input label="Transfer amount" type="number" step="0.01" min="0.01" required value={f.transfer_amt} onChange={set('transfer_amt')} />
          </fieldset>
          <fieldset className="grid gap-3 sm:grid-cols-2">
            <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Nationality</legend>
            <Input label="Nationality" required value={f.nationality} onChange={set('nationality')} />
            <Input label="Nationality ISO" required value={f.nationality_iso} onChange={set('nationality_iso')} maxLength={3} />
          </fieldset>
          <PlaceFields label="Birth place" value={f.birth_place} onChange={(p) => setF({ ...f, birth_place: p })} />
          <fieldset className="grid gap-3 sm:grid-cols-2">
            <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Address</legend>
            <Input label="Street" required value={f.street_num} onChange={set('street_num')} />
            <Input label="Additional address" value={f.additional_address} onChange={set('additional_address')} />
            <Input label="City" required value={f.city} onChange={set('city')} />
            <Input label="State" required value={f.state} onChange={set('state')} />
            <Input label="Postal code" required value={f.postal_code} onChange={set('postal_code')} />
            <Input label="Country" required value={f.country} onChange={set('country')} />
            <Input label="Country ISO" required value={f.country_iso} onChange={set('country_iso')} maxLength={3} />
          </fieldset>
          <div className="flex justify-end"><Button type="submit" loading={saving}>Save payer</Button></div>
        </form>
      </Card>
      <Card title="Payers">
        {isLoading && <div className="h-16 animate-pulse rounded-lg bg-white/40" />}
        {!isLoading && (!payers || payers.length === 0) && <p className="text-sm text-muted">No payers added yet.</p>}
        <ul className="space-y-2">
          {payers?.map((p) => (
            <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/40 bg-white/25 px-3 py-2 text-sm">
              <span className="font-semibold">{p.first_name} {p.last_name}</span>
              <span className="text-muted">{p.email}</span>
              <span className="text-muted">{p.relationship_to_student ?? '—'}</span>
              <span className="text-muted">{p.transfer_amt ?? '—'}</span>
              <span className="text-muted">{fmtDate(p.created_at)}</span>
              <Badge tone={p.edubao_payer_id ? 'green' : 'gray'}>{p.payer_account_id ?? 'pending'}</Badge>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
