import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartCard } from './ChartCard'

export function BarChartCard({ title, data }: { title: string; data: { name: string; value: number }[] }) {
  return (
    <ChartCard title={title}>
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#fee4cc" vertical={false} />
          <XAxis dataKey="name" stroke="#71624d" fontSize={12} />
          <YAxis allowDecimals={false} stroke="#71624d" fontSize={12} />
          <Tooltip cursor={{ fill: '#fff7ed' }} />
          <Bar dataKey="value" fill="#ff5a00" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
