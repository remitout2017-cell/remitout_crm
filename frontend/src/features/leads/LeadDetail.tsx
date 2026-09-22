import { useState } from 'react'
import { FiArrowLeft } from 'react-icons/fi'
import { Link, useParams } from 'react-router-dom'
import { Badge } from '../../components/ui/Badge'
import { statusTone } from '../../utils/status'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { Stepper } from '../../components/ui/Stepper'
import { Tabs } from '../../components/ui/Tabs'
import { useGetLeadQuery } from './api'
import { fmtDate } from '../../utils/cn'
import { StepsPanel } from './StepsPanel'
import { DocumentsPanel } from './DocumentsPanel'
import { PayersPanel } from './PayersPanel'
import { VerificationPanel } from './VerificationPanel'
import { ReferencePanel } from './ReferencePanel'

const Field = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <div><dt className="text-xs text-muted">{label}</dt><dd className="font-medium">{value ?? '—'}</dd></div>
)

const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'steps', label: 'Application steps' },
  { key: 'documents', label: 'Documents' },
  { key: 'payers', label: 'Payers' },
  { key: 'verify', label: 'Verification' },
  { key: 'reference', label: 'Reference data' },
]

export default function LeadDetail() {
  const { id } = useParams()
  const { data: lead, isLoading: loading } = useGetLeadQuery(Number(id))
  const [tab, setTab] = useState('overview')
  if (loading) return <div className="glass h-40 animate-pulse rounded-2xl" />
  if (!lead) return <Link to="/leads" className="text-brand-600">Lead not found — back to leads</Link>

  return (
    <>
      <Link to="/leads" className="mb-3 inline-flex items-center gap-1 text-sm text-muted hover:text-brand-600"><FiArrowLeft /> Leads</Link>
      <PageHeader title={`Lead #${lead.id}`} subtitle={lead.account_id ?? 'Not yet submitted to Edubao'}
        action={<Badge tone={statusTone(lead.status)}>{lead.status}</Badge>} />
      <Card className="mb-4">
        <Stepper steps={['Contact', 'Passport', 'Account', 'Terms']} current={Math.min(lead.current_step + 1, 4)} />
      </Card>
      <div className="mb-4"><Tabs items={TABS} active={tab} onChange={setTab} /></div>

      {tab === 'overview' && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Details">
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <Field label="Student" value={`#${lead.student_id}`} />
              <Field label="Edubao lead" value={lead.edubao_lead_id} />
              <Field label="Expected arrival" value={fmtDate(lead.expected_date_arrival)} />
              <Field label="Blocked amount" value={lead.blocked_acc_amt} />
              <Field label="Duration (months)" value={lead.blocked_acc_duration} />
              <Field label="Terms accepted" value={lead.terms_accepted ? 'Yes' : 'No'} />
            </dl>
          </Card>
          <Card title="Submission history">
            <ul className="space-y-2 text-sm">
              {lead.submissions.length === 0 && <li className="text-muted">No submissions yet.</li>}
              {lead.submissions.map((s, i) => (
                <li key={i} className="flex items-center justify-between">
                  <span>Step {s.step} · {fmtDate(s.created_at)}</span>
                  <Badge tone={s.success ? 'green' : 'red'}>{s.success ? 'success' : 'failed'}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}
      {tab === 'steps' && <StepsPanel lead={lead} />}
      {tab === 'documents' && <DocumentsPanel leadId={lead.id} />}
      {tab === 'payers' && <PayersPanel leadId={lead.id} />}
      {tab === 'verify' && <VerificationPanel leadId={lead.id} />}
      {tab === 'reference' && <ReferencePanel partnerAccountId={lead.partner_account_id} />}
    </>
  )
}
