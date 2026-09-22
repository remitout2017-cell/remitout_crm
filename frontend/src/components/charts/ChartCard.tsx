import { Card } from '../ui/Card'

export function ChartCard({ title, children }: { title: string; children: React.ReactElement }) {
  return <Card title={title}><div className="h-64">{children}</div></Card>
}
