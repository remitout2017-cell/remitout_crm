import { useState } from 'react'
import toast from 'react-hot-toast'
import { FiPlus, FiRefreshCw } from 'react-icons/fi'
import { useNavigate } from 'react-router-dom'
import { Badge } from '../../components/ui/Badge'
import { statusTone } from '../../utils/status'
import { Button } from '../../components/ui/Button'
import { DataTable } from '../../components/ui/DataTable'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { Select } from '../../components/ui/Select'
import { useAddLeadMutation, useGetLeadsQuery } from './api'
import { useGetStudentsQuery } from '../students/api'
import { useGetPartnersQuery } from '../partners/api'
import { useGetFormDataQuery } from '../reference/api'
import { errorMessage } from '../../store/baseApi'
import { fmtDate } from '../../utils/cn'

export default function Leads() {
  const nav = useNavigate()
  const { data, isLoading: loading } = useGetLeadsQuery()
  const students = useGetStudentsQuery()
  const partners = useGetPartnersQuery()
  const onboardedPartners = partners.data?.filter((p) => p.onboarded && p.is_active) ?? []
  const [addLead, { isLoading: saving }] = useAddLeadMutation()
  const [open, setOpen] = useState(false)
  const [f, setF] = useState({ student_id: '', partner_account_id: '', app_type: '', expected_date_arrival: '' })
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value })

  const formData = useGetFormDataQuery(Number(f.partner_account_id), { skip: !f.partner_account_id })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const lead = await addLead({
        student_id: +f.student_id, partner_account_id: +f.partner_account_id,
        app_type: +f.app_type, expected_date_arrival: f.expected_date_arrival,
      }).unwrap()
      toast.success('Lead created')
      setOpen(false); nav(`/leads/${lead.id}`)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <>
      <PageHeader title="Leads" subtitle="Blocked-account applications"
        action={<Button icon={<FiPlus />} onClick={() => setOpen(true)}>New lead</Button>} />
      <DataTable rows={data} loading={loading} rowKey={(l) => l.id} onRowClick={(l) => nav(`/leads/${l.id}`)}
        columns={[
          { header: 'ID', cell: (l) => `#${l.id}` },
          { header: 'Account', cell: (l) => l.account_id ?? '—' },
          { header: 'Student', cell: (l) => `#${l.student_id}` },
          { header: 'Step', cell: (l) => `${l.current_step} / 4` },
          { header: 'Status', cell: (l) => <Badge tone={statusTone(l.status)}>{l.status}</Badge> },
          { header: 'Arrival', cell: (l) => fmtDate(l.expected_date_arrival) },
        ]} />
      <Modal open={open} title="New lead" onClose={() => setOpen(false)}>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
          <Select label="Student" required value={f.student_id} onChange={set('student_id')}>
            <option value="">Select…</option>
            {students.data?.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
          </Select>
          <Select label="Partner account" required value={f.partner_account_id} onChange={set('partner_account_id')}>
            <option value="">Select…</option>
            {onboardedPartners.map((p) => <option key={p.id} value={p.id}>{p.name} (#{p.id})</option>)}
          </Select>
          {onboardedPartners.length === 0 && !partners.isLoading && (
            <p className="text-xs text-muted sm:col-span-2">
              No onboarded partner accounts yet — onboard one on the <span className="font-semibold">Partners</span> page first.
            </p>
          )}
          <Input label="App type" type="number" required value={f.app_type} onChange={set('app_type')} />
          <Input label="Expected arrival" type="date" required value={f.expected_date_arrival} onChange={set('expected_date_arrival')} />

          {f.partner_account_id && (
            <div className="rounded-lg border border-white/40 bg-white/25 p-3 text-xs sm:col-span-2">
              <div className="mb-2 flex items-center justify-between">
                <span className="font-semibold text-muted">App type codes (Edubao form-required-data)</span>
                <button type="button" onClick={() => formData.refetch()} className="text-muted hover:text-brand-600">
                  <FiRefreshCw className={formData.isFetching ? 'animate-spin' : undefined} />
                </button>
              </div>
              {formData.isLoading && <div className="h-16 animate-pulse rounded bg-white/40" />}
              {!formData.isLoading && (
                <pre className="max-h-40 overflow-auto whitespace-pre-wrap">{JSON.stringify(formData.data ?? {}, null, 2)}</pre>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Create</Button>
          </div>
        </form>
      </Modal>
    </>
  )
}
