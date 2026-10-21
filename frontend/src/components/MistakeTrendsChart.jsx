import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const series = [
  { key: 'reliability', label: 'Reliability', color: '#7770d8' },
  { key: 'security', label: 'Security', color: '#e68582' },
  { key: 'maintainability', label: 'Maintainability', color: '#69a9a0' },
]

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 shadow-lg">
      <p className="mb-2 text-[10px] font-semibold text-slate-500">Week of {label}</p>
      {payload.map((item) => <p key={item.dataKey} className="flex items-center gap-2 py-0.5 text-[11px] text-slate-700"><span className="size-2 rounded-full" style={{ background: item.color }} />{item.name}<span className="ml-4 font-semibold">{item.value}</span></p>)}
    </div>
  )
}

export default function MistakeTrendsChart({ compact = false, trends = [], categories = [] }) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_185px]">
      <div className="min-w-0">
        <div className="mb-4 flex flex-wrap gap-x-5 gap-y-2">
          {series.map((item) => <span key={item.key} className="flex items-center gap-2 text-[10px] font-medium text-slate-500"><span className="size-2 rounded-full" style={{ backgroundColor: item.color }} />{item.label}</span>)}
        </div>
        <div className={compact ? 'h-[220px] w-full' : 'h-[285px] w-full'}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trends} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#eef1ef" strokeDasharray="3 5" vertical={false} />
              <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} dy={10} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip content={<ChartTooltip />} cursor={{ stroke: '#dce4df', strokeDasharray: '4 4' }} />
              {series.map((item) => <Line key={item.key} type="monotone" dataKey={item.key} name={item.label} stroke={item.color} strokeWidth={2.4} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />)}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      {!compact && <div className="border-t border-slate-100 pt-4 xl:border-l xl:border-t-0 xl:pl-5 xl:pt-0">
        <p className="mb-4 text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-400">Top categories</p>
        <div className="space-y-4">
          {categories.map((category) => <div key={category.label}>
            <div className="mb-1.5 flex items-center justify-between text-[11px]"><span className="text-slate-600">{category.label}</span><span className="font-semibold text-slate-700">{category.count}</span></div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-violet-500" style={{ width: `${Math.min(100, category.count)}%` }} /></div>
          </div>)}
        </div>
      </div>}
    </div>
  )
}
