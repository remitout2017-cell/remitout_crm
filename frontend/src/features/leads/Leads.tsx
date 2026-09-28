import { useState } from 'react'
import toast from 'react-hot-toast'
import { FiEdit2, FiPlus, FiTrash2 } from 'react-icons/fi'
import { useNavigate } from 'react-router-dom'
import { Badge } from '../../components/ui/Badge'
import { statusTone } from '../../utils/status'
import { Button } from '../../components/ui/Button'
import { DataTable } from '../../components/ui/DataTable'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { Select } from '../../components/ui/Select'
import { useAddLeadMutation, useDeleteLeadMutation, useGetLeadsQuery, useUpdateLeadMutation } from './api'
import { useGetStudentsQuery } from '../students/api'
import { useGetPartnersQuery } from '../partners/api'
import { useGetFormDataQuery } from '../reference/api'
import { errorMessage } from '../../store/baseApi'
import { fmtDate } from '../../utils/cn'
import type { Lead } from '../../types'

const empty = { student_id: '', partner_account_id: '', app_type: '', expected_date_arrival: '' }

export default function Leads() {
  const nav = useNavigate()
  const { data, isLoading: loading } = useGetLeadsQuery()
  const students = useGetStudentsQuery()
  const partners = useGetPartnersQuery()
  const onboardedPartners = partners.data?.filter((p) => p.onboarded && p.is_active) ?? []
  const [addLead, { isLoading: adding }] = useAddLeadMutation()
  const [updateLead, { isLoading: updating }] = useUpdateLeadMutation()
  const [deleteLead, { isLoading: deleting }] = useDeleteLeadMutation()
  const saving = adding || updating
  const [editing, setEditing] = useState<Lead | null>(null)
  const [open, setOpen] = useState(false)
  const [f, setF] = useState(empty)
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value })

  const formData = useGetFormDataQuery(Number(f.partner_account_id), { skip: !f.partner_account_id })
  const appTypes: { id: number; title: string }[] = (formData.data as { visa_app_types?: { id: number; title: string }[] } | undefined)?.visa_app_types ?? []

  const openCreate = () => { setEditing(null); setF(empty); setOpen(true) }
  const openEdit = (l: Lead) => {
    setEditing(l)
    setF({ student_id: String(l.student_id), partner_account_id: String(l.partner_account_id), app_type: String(l.app_type ?? ''), expected_date_arrival: l.expected_date_arrival ?? '' })
    setOpen(true)
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editing) {
        await updateLead({ id: editing.id, body: { app_type: +f.app_type, expected_date_arrival: f.expected_date_arrival } }).unwrap()
        toast.success('Lead updated')
        setOpen(false)
      } else {
        const lead = await addLead({
          student_id: +f.student_id, partner_account_id: +f.partner_account_id,
          app_type: +f.app_type, expected_date_arrival: f.expected_date_arrival,
        }).unwrap()
        toast.success('Lead created')
        setOpen(false); nav(`/leads/${lead.id}`)
      }
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const remove = async (l: Lead) => {
    if (!window.confirm(`Delete lead #${l.id}? This removes its documents, payers and submission history too.`)) return
    try {
      await deleteLead(l.id).unwrap()
      toast.success('Lead deleted')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <>
      <PageHeader title="Leads" subtitle="Blocked-account applications"
        action={<Button icon={<FiPlus />} onClick={openCreate}>New lead</Button>} />
      <DataTable rows={data} loading={loading} rowKey={(l) => l.id} onRowClick={(l) => nav(`/leads/${l.id}`)}
        columns={[
          { header: 'ID', cell: (l) => `#${l.id}` },
          { header: 'Account', cell: (l) => l.account_id ?? '—' },
          { header: 'Student', cell: (l) => `#${l.student_id}` },
          { header: 'Step', cell: (l) => `${l.current_step} / 4` },
          { header: 'Status', cell: (l) => <Badge tone={statusTone(l.status)}>{l.status}</Badge> },
          { header: 'Arrival', cell: (l) => fmtDate(l.expected_date_arrival) },
          { header: '', cell: (l) => (
            <div className="flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
              <button type="button" title="Edit" className="text-muted hover:text-brand-600" onClick={() => openEdit(l)}>
                <FiEdit2 />
              </button>
              <button type="button" title="Delete" disabled={deleting} className="text-muted hover:text-red-600 disabled:opacity-50"
                onClick={() => remove(l)}>
                <FiTrash2 />
              </button>
            </div>
          ) },
        ]} />
      <Modal open={open} title={editing ? `Edit lead #${editing.id}` : 'New lead'} onClose={() => setOpen(false)}>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
          <Select label="Student" required value={f.student_id} onChange={set('student_id')} disabled={!!editing}>
            <option value="">Select…</option>
            {students.data?.map((s) => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
          </Select>
          <Select label="Partner account" required value={f.partner_account_id} onChange={set('partner_account_id')} disabled={!!editing}>
            <option value="">Select…</option>
            {onboardedPartners.map((p) => <option key={p.id} value={p.id}>{p.name} (#{p.id})</option>)}
          </Select>
          {!editing && onboardedPartners.length === 0 && !partners.isLoading && (
            <p className="text-xs text-muted sm:col-span-2">
              No onboarded partner accounts yet — onboard one on the <span className="font-semibold">Partners</span> page first.
            </p>
          )}
          {editing && (
            <p className="text-xs text-muted sm:col-span-2">
              Student and partner account are fixed once a lead is created (Edubao already has step 1). Only app type and arrival date can be edited here.
            </p>
          )}
          <Select label="App type" required value={f.app_type} onChange={set('app_type')} disabled={!f.partner_account_id && !editing}>
            <option value="">{formData.isFetching ? 'Loading…' : 'Select…'}</option>
            {appTypes.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
          </Select>
          <Input label="Expected arrival" type="date" required value={f.expected_date_arrival} onChange={set('expected_date_arrival')} />

          <div className="flex justify-end gap-2 sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>{editing ? 'Save' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </>
  )
}
