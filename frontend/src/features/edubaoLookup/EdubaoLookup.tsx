import { useState } from 'react'
import toast from 'react-hot-toast'
import { FiSearch } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { PageHeader } from '../../components/ui/PageHeader'
import { Select } from '../../components/ui/Select'
import { errorMessage } from '../../store/baseApi'
import { useGetPartnersQuery } from '../partners/api'
import { field, useLazyGetEdubaoLeadQuery } from './api'

const fmtSize = (b: number) => (b < 1024 ? `${b} B` : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`)

export default function EdubaoLookup() {
  const partners = useGetPartnersQuery()
  const onboardedPartners = partners.data?.filter((p) => p.onboarded && p.is_active) ?? []
  const [accountId, setAccountId] = useState('')
  const [leadId, setLeadId] = useState('')
  const [edubaoAccountId, setEdubaoAccountId] = useState('')
  const [trigger, { data: lead, isFetching, isError, error }] = useLazyGetEdubaoLeadQuery()

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!accountId || (!leadId && !edubaoAccountId)) return
    trigger({ accountId: +accountId, leadId: leadId ? +leadId : undefined, edubaoAccountId: edubaoAccountId || undefined })
      .unwrap()
      .catch((err) => toast.error(errorMessage(err)))
  }

  const documents = (lead?.documents as { doc_id: string; name: string; url: string; doc_type: string; mimetype: string; size: number; status_name: string }[] | undefined) ?? []
  const payers = (lead?.payers as { payer_id: number; name: string; relationship: string; transfer_amt: string; email_id: string }[] | undefined) ?? []
  const bankAccounts = (lead?.bank_accounts as { holder_name: string; iban_number: string; bic_swift_code: string; bank_name: string }[] | undefined) ?? []

  return (
    <>
      <PageHeader title="Edubao Lookup" subtitle="Fetch a lead's live record straight from Edubao (Get Individual Lead)" />

      <Card title="Find a lead">
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-4 sm:items-end">
          <Select label="Partner account" required value={accountId} onChange={(e) => setAccountId(e.target.value)}>
            <option value="">Select…</option>
            {onboardedPartners.map((p) => <option key={p.id} value={p.id}>{p.name} (#{p.id})</option>)}
          </Select>
          <Input label="Lead ID" placeholder="1880" inputMode="numeric" value={leadId}
            onChange={(e) => setLeadId(e.target.value.replace(/\D/g, ''))} />
          <Input label="or Edubao account ID" placeholder="CX-01-BA-1235" value={edubaoAccountId}
            onChange={(e) => setEdubaoAccountId(e.target.value)} />
          <Button type="submit" icon={<FiSearch />} loading={isFetching}>Fetch</Button>
        </form>
        {onboardedPartners.length === 0 && !partners.isLoading && (
          <p className="mt-2 text-xs text-muted">No onboarded partner accounts yet — onboard one on the Partners page first.</p>
        )}
        <p className="mt-2 text-xs text-muted">Provide either a Lead ID or an Edubao account ID (e.g. CX-01-BA-1235).</p>
      </Card>

      {isError && (
        <Card className="mt-4">
          <p className="text-sm text-red-600">{errorMessage(error)}</p>
        </Card>
      )}

      {lead && !isError && (
        <div className="mt-4 space-y-4">
          <Card title="Applicant">
            <div className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
              <div><span className="text-muted">Name</span><br />{field(lead, 'title')} {field(lead, 'first_name')} {field(lead, 'last_name')}</div>
              <div><span className="text-muted">Lead ID</span><br />{field(lead, 'lead_id')}</div>
              <div><span className="text-muted">Account ID</span><br />{field(lead, 'account_id')}</div>
              <div><span className="text-muted">Email</span><br />{field(lead, 'email_id')}</div>
              <div><span className="text-muted">Mobile</span><br />+{field(lead, 'phone_code')} {field(lead, 'mobile_no')}</div>
              <div>
                <span className="text-muted">KYC result</span><br />
                <Badge tone={lead.kyc_result_status === 'accept' ? 'green' : lead.kyc_result_status === 'reject' ? 'red' : 'gray'}>
                  {field(lead, 'kyc_result_status')}
                </Badge>
              </div>
            </div>
          </Card>

          <Card title="Blocked account & fees">
            <div className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
              <div><span className="text-muted">Amount</span><br />{field(lead, 'blocked_acc_amt')}</div>
              <div><span className="text-muted">Duration (months)</span><br />{field(lead, 'blocked_acc_duration')}</div>
              <div><span className="text-muted">Visa doc type</span><br />{field(lead, 'visa_eligibility_doc_type')}</div>
              <div><span className="text-muted">Setup fee</span><br />{field(lead, 'setup_fee')}</div>
              <div><span className="text-muted">Monthly fee</span><br />{field(lead, 'monthly_fee')}</div>
              <div><span className="text-muted">Buffer amount</span><br />{field(lead, 'buffer_amount')}</div>
              <div><span className="text-muted">Total deposit</span><br />{field(lead, 'total_deposit')}</div>
            </div>
          </Card>

          <Card title={`Documents (${documents.length})`}>
            {documents.length === 0 && <p className="text-sm text-muted">No documents on this lead.</p>}
            <ul className="space-y-2">
              {documents.map((d) => (
                <li key={d.doc_id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
                  <span className="font-semibold">{d.doc_type}</span>
                  <span className="text-muted">{d.name} · {fmtSize(d.size)}</span>
                  <Badge tone={d.status_name === 'Accepted' ? 'green' : 'gray'}>{d.status_name}</Badge>
                </li>
              ))}
            </ul>
          </Card>

          <Card title={`Payers (${payers.length})`}>
            {payers.length === 0 && <p className="text-sm text-muted">No payers on this lead.</p>}
            <ul className="space-y-2">
              {payers.map((p) => (
                <li key={p.payer_id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
                  <span className="font-semibold">{p.name}</span>
                  <span className="text-muted">{p.relationship} · {p.email_id}</span>
                  <span className="text-muted">{p.transfer_amt}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card title={`Bank accounts (${bankAccounts.length})`}>
            {bankAccounts.length === 0 && <p className="text-sm text-muted">No blocked-account bank details returned yet.</p>}
            <ul className="space-y-2">
              {bankAccounts.map((b, i) => (
                <li key={i} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
                  <span className="font-semibold">{b.holder_name}</span>
                  <span className="text-muted">{b.bank_name}</span>
                  <span className="text-muted">{b.iban_number}</span>
                  <span className="text-muted">{b.bic_swift_code}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card title="Raw response">
            <pre className="max-h-96 overflow-auto rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs">
              {JSON.stringify(lead, null, 2)}
            </pre>
          </Card>
        </div>
      )}
    </>
  )
}
