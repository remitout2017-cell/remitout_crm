import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { FiEdit2, FiPlus } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { statusTone } from '../../utils/status'
import { Button } from '../../components/ui/Button'
import { DataTable } from '../../components/ui/DataTable'
import { Autocomplete } from '../../components/ui/Autocomplete'
import { Input } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
import { PageHeader } from '../../components/ui/PageHeader'
import { Select } from '../../components/ui/Select'
import { useAddStudentMutation, useGetStudentsQuery, useUpdateStudentMutation } from './api'
import { useGetCountriesQuery } from '../reference/api'
import { errorMessage } from '../../store/baseApi'
import type { Student, StudentInput } from '../../types'
import { fmtDate } from '../../utils/cn'
import { ALL_CITIES, INDIA_PLACES, INDIA_STATES } from './indiaPlaces'

// Edubao's step 1 needs every one of these on the student (values match its form-required-data lists).
const TITLES = ['Mr', 'Mrs', 'Ms', 'Mx']
const GENDERS = ['Male', 'Female', 'Prefer not to say', 'Diverse']
// Title-case each word, e.g. "united states" -> "United States".
const toTitleCase = (v: string) => v.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase())
const COUNTRY_ISO_PATTERN = /^[A-Z]{3}$/
const empty: StudentInput = {
  first_name: '', last_name: '', email: '', mobile_no: '', title: '', gender: '', phone_code: '', street_num: '',
  additional_address: '', postal_code: '', city: '', state: '', country: '', country_iso: '',
}
const toForm = (s: Student): StudentInput => ({
  ...empty,
  ...Object.fromEntries(Object.keys(empty).map((k) => [k, (s as unknown as Record<string, string | null>)[k] ?? ''])),
})

export default function Students() {
  const { data, isLoading: loading } = useGetStudentsQuery()
  const [addStudent, { isLoading: adding }] = useAddStudentMutation()
  const [updateStudent, { isLoading: updating }] = useUpdateStudentMutation()
  const saving = adding || updating
  const [editing, setEditing] = useState<number | null>(null)
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(empty)
  // Cities narrow to the chosen state once it matches a known one; otherwise suggest all.
  const cityOptions = INDIA_PLACES[form.state ?? ''] ?? ALL_CITIES
  const set = (k: keyof StudentInput) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [k]: e.target.value })

  const countryIso = form.country_iso ?? ''
  const countryIsoError = countryIso !== '' && !COUNTRY_ISO_PATTERN.test(countryIso)
    ? 'Must be 3 letters, e.g. IND (ISO alpha-3 code)' : undefined

  // Debounce so we don't hit the backend on every keystroke.
  const [countryQuery, setCountryQuery] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setCountryQuery((form.country ?? '').trim()), 200)
    return () => clearTimeout(t)
  }, [form.country])
  const { data: countryMatches } = useGetCountriesQuery(countryQuery, { skip: countryQuery === '' })
  const countryOptions = (countryMatches ?? []).map((c) => c.name)
  const pickCountry = (name: string) => {
    const match = countryMatches?.find((c) => c.name === name)
    setForm({ ...form, country: toTitleCase(name), country_iso: match ? match.iso3 : form.country_iso })
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (countryIsoError) return
    try {
      // Blank optional fields are dropped so they don't overwrite/violate anything.
      const body = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== '')) as StudentInput
      if (editing) await updateStudent({ id: editing, body }).unwrap()
      else await addStudent(body).unwrap()
      toast.success(editing ? 'Student updated' : 'Student added')
      setOpen(false); setForm(empty); setEditing(null)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <>
      <PageHeader title="Students" subtitle="People applying for a blocked account"
        action={<Button icon={<FiPlus />} onClick={() => { setEditing(null); setForm(empty); setOpen(true) }}>Add student</Button>} />
      <DataTable rows={data} loading={loading} rowKey={(s) => s.id}
        columns={[
          { header: 'Name', cell: (s) => <span className="font-semibold">{s.first_name} {s.last_name}</span> },
          { header: 'Email', cell: (s) => s.email },
          { header: 'Mobile', cell: (s) => s.mobile_no },
          { header: 'Status', cell: (s) => <Badge tone={statusTone(s.status)}>{s.status}</Badge> },
          { header: 'Added', cell: (s) => fmtDate(s.created_at) },
          { header: '', cell: (s) => (
            <button type="button" title="Edit" className="text-muted hover:text-brand-600"
              onClick={() => { setEditing(s.id); setForm(toForm(s)); setOpen(true) }}><FiEdit2 /></button>
          ) },
        ]} />
      <Modal open={open} title={editing ? 'Edit student' : 'Add student'} onClose={() => setOpen(false)}>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
          <Input label="First name" placeholder="Raju" required value={form.first_name} onChange={set('first_name')} />
          <Input label="Last name" placeholder="Kale" required value={form.last_name} onChange={set('last_name')} />
          <Input label="Email" type="email" placeholder="raju@example.com" required value={form.email} onChange={set('email')} />
          <Select label="Title" value={form.title ?? ''} onChange={set('title')}>
            <option value="">Select…</option>{TITLES.map((t) => <option key={t}>{t}</option>)}
          </Select>
          <Select label="Gender" value={form.gender ?? ''} onChange={set('gender')}>
            <option value="">Select…</option>{GENDERS.map((g) => <option key={g}>{g}</option>)}
          </Select>
          <Input label="Phone code" placeholder="91" value={form.phone_code ?? ''} onChange={set('phone_code')} />
          <Input label="Mobile (10 digits)" placeholder="9369902400" required inputMode="numeric" pattern="\d{10}" maxLength={10} title="Exactly 10 digits, without the country code"
            value={form.mobile_no} onChange={(e) => setForm({ ...form, mobile_no: e.target.value.replace(/\D/g, '') })} />
          <Input label="Street" placeholder="Laxmi Nager" value={form.street_num ?? ''} onChange={set('street_num')} />
          <Input label="Additional address" placeholder="Apartment, suite, etc." value={form.additional_address ?? ''} onChange={set('additional_address')} />
          <Input label="Postal code" placeholder="400096" value={form.postal_code ?? ''} onChange={set('postal_code')} />
          <Autocomplete label="City" placeholder="Mumbai" value={form.city ?? ''} options={cityOptions} onChange={(v) => setForm({ ...form, city: v })} />
          <Autocomplete label="State" placeholder="Maharashtra" value={form.state ?? ''} options={INDIA_STATES} onChange={(v) => setForm({ ...form, state: v })} />
          <Autocomplete label="Country" placeholder="India" value={form.country ?? ''} options={countryOptions}
            onChange={pickCountry} />
          <Input label="Country ISO" placeholder="IND" maxLength={3} pattern="[A-Z]{3}" title="3-letter ISO alpha-3 code, e.g. IND"
            error={countryIsoError} value={countryIso}
            onChange={(e) => setForm({ ...form, country_iso: e.target.value.toUpperCase().replace(/[^A-Z]/g, '') })} />
          <div className="flex justify-end gap-2 sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>
    </>
  )
}
