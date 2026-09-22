import { FiFileText, FiCheckCircle, FiUsers, FiBriefcase } from 'react-icons/fi'
import { BarChartCard } from '../../components/charts/BarChartCard'
import { DonutChartCard } from '../../components/charts/DonutChartCard'
import { PageHeader } from '../../components/ui/PageHeader'
import { StatCard } from '../../components/ui/StatCard'
import { useGetLeadsQuery } from '../leads/api'
import { useGetStudentsQuery } from '../students/api'

const count = (items: string[]) =>
  Object.entries(items.reduce<Record<string, number>>((a, k) => ({ ...a, [k]: (a[k] ?? 0) + 1 }), {}))
    .map(([name, value]) => ({ name, value }))

export default function Dashboard() {
  const students = useGetStudentsQuery().data ?? []
  const leads = useGetLeadsQuery().data ?? []

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Blocked-account pipeline overview" />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Students" value={students.length} icon={FiUsers} />
        <StatCard label="Leads" value={leads.length} icon={FiFileText} />
        <StatCard label="Completed" value={leads.filter((l) => l.current_step >= 4).length} icon={FiCheckCircle} />
        <StatCard label="Partners used" value={new Set(leads.map((l) => l.partner_account_id)).size} icon={FiBriefcase} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <BarChartCard title="Leads by step" data={count(leads.map((l) => `Step ${l.current_step}`))} />
        <DonutChartCard title="Leads by status" data={count(leads.map((l) => l.status))} />
      </div>
    </>
  )
}
