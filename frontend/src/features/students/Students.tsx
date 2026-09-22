import { useState } from 'react'
import toast from 'react-hot-toast'
import { FiPlus } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { statusTone } from '../../utils/status'
import { Button } from '../../components/ui/Button'
import { DataTable } from '../../components/ui/DataTable'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { useAddStudentMutation, useGetStudentsQuery } from './api'
import { errorMessage } from '../../store/baseApi'
import type { StudentInput } from '../../types'
import { fmtDate } from '../../utils/cn'

const empty: StudentInput = { first_name: '', last_name: '', email: '', mobile_no: '' }

export default function Students() {
  const { data, isLoading: loading } = useGetStudentsQuery()
  const [addStudent, { isLoading: saving }] = useAddStudentMutation()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(empty)
  const set = (k: keyof StudentInput) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await addStudent(form).unwrap()
      toast.success('Student added')
      setOpen(false); setForm(empty)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <>
      <PageHeader title="Students" subtitle="People applying for a blocked account"
        action={<Button icon={<FiPlus />} onClick={() => setOpen(true)}>Add student</Button>} />
      <DataTable rows={data} loading={loading} rowKey={(s) => s.id}
        columns={[
          { header: 'Name', cell: (s) => <span className="font-semibold">{s.first_name} {s.last_name}</span> },
          { header: 'Email', cell: (s) => s.email },
          { header: 'Mobile', cell: (s) => s.mobile_no },
          { header: 'Status', cell: (s) => <Badge tone={statusTone(s.status)}>{s.status}</Badge> },
          { header: 'Added', cell: (s) => fmtDate(s.created_at) },
        ]} />
      <Modal open={open} title="Add student" onClose={() => setOpen(false)}>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
          <Input label="First name" required value={form.first_name} onChange={set('first_name')} />
          <Input label="Last name" required value={form.last_name} onChange={set('last_name')} />
          <Input label="Email" type="email" required value={form.email} onChange={set('email')} />
          <Input label="Mobile" required value={form.mobile_no} onChange={set('mobile_no')} />
          <div className="flex justify-end gap-2 sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>
    </>
  )
}
