import { useState } from 'react'
import toast from 'react-hot-toast'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { PageHeader } from '../../components/ui/PageHeader'
import { Select } from '../../components/ui/Select'
import { useAppDispatch, useAppSelector } from '../../store'
import { useRetryTokenMutation, useStartOnboardingMutation, useVerifyOnboardingMutation } from './api'
import { setPartner } from './slice'
import { errorMessage } from '../../store/baseApi'

/** Two-step Edubao onboarding: credentials → emailed OTP. Progress lives in the Redux store. */
export default function Partners() {
  const dispatch = useAppDispatch()
  const partner = useAppSelector((s) => s.onboarding.partner)
  const [start, { isLoading: starting }] = useStartOnboardingMutation()
  const [verify, { isLoading: verifying }] = useVerifyOnboardingMutation()
  const [retry, { isLoading: retrying }] = useRetryTokenMutation()
  const [form, setForm] = useState({ name: '', environment: 'staging' as 'staging' | 'production', login_email: '', password: '' })
  const [otp, setOtp] = useState('')

  const onStart = async (e: React.FormEvent) => {
    e.preventDefault()
    try { dispatch(setPartner(await start(form).unwrap())); toast.success('OTP sent to partner email') }
    catch (err) { toast.error(errorMessage(err)) }
  }
  const onVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!partner) return
    try { dispatch(setPartner(await verify({ id: partner.id, otp }).unwrap())); toast.success('Partner onboarded') }
    catch (err) { toast.error(errorMessage(err)) }
  }
  const onRetry = async () => {
    if (!partner) return
    try { dispatch(setPartner(await retry(partner.id).unwrap())); toast.success('Access token issued') }
    catch (err) { toast.error(errorMessage(err)) }
  }
  const hasToken = !!partner?.access_token_expires_at

  return (
    <>
      <PageHeader title="Partners" subtitle="Onboard an Edubao partner account" />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="1. Credentials">
          <form className="space-y-3" onSubmit={onStart}>
            <Input label="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Select label="Environment" value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value as 'staging' | 'production' })}>
              <option value="staging">Staging</option><option value="production">Production</option>
            </Select>
            <Input label="Login email" type="email" required value={form.login_email} onChange={(e) => setForm({ ...form, login_email: e.target.value })} />
            <Input label="Password" type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <Button type="submit" loading={starting}>Send OTP</Button>
          </form>
        </Card>
        <Card title="2. Verify OTP">
          {partner ? (
            <form className="space-y-3" onSubmit={onVerify}>
              <p className="text-sm text-muted">Account #{partner.id} · {partner.login_email}</p>
              <Input label="OTP" required value={otp} onChange={(e) => setOtp(e.target.value)} />
              <Button type="submit" loading={verifying}>Verify</Button>
              {partner.onboarded && hasToken && <Badge tone="green">Onboarded · {partner.partner_key}</Badge>}
              {partner.onboarded && !hasToken && (
                <div className="space-y-2">
                  <Badge tone="brand">Credentials saved · access token pending</Badge>
                  <p className="text-xs text-muted">Edubao issued credentials but rejected the token request. No new OTP is needed — retry once Edubao has activated the OAuth client.</p>
                  <Button type="button" variant="secondary" loading={retrying} onClick={onRetry}>Retry token</Button>
                </div>
              )}
            </form>
          ) : <p className="text-sm text-muted">Complete step 1 first.</p>}
        </Card>
      </div>
    </>
  )
}
