import Icon from './Icon.jsx'

const styles = {
  violet: { icon: 'bg-violet-50 text-violet-600', change: 'text-emerald-700' },
  blue: { icon: 'bg-sky-50 text-sky-600', change: 'text-emerald-700' },
  rose: { icon: 'bg-rose-50 text-rose-600', change: 'text-emerald-700' },
  green: { icon: 'bg-emerald-50 text-emerald-700', change: 'text-emerald-700' },
}

export default function StatCard({ metric }) {
  const tone = styles[metric.tone] ?? styles.green
  const negative = metric.change.startsWith('-')
  return (
    <article className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_8px_rgba(15,23,42,0.025)] sm:p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[12px] font-medium text-slate-500">{metric.label}</p>
          <p className="mt-3 text-[29px] font-semibold leading-none tracking-[-0.04em] text-slate-900">{metric.value}</p>
        </div>
        <span className={`grid size-10 place-items-center rounded-xl ${tone.icon}`}><Icon name={metric.icon} size={19} /></span>
      </div>
      <div className="mt-4 flex items-center gap-2 text-[10px]">
        <span className={`font-semibold ${negative ? 'text-emerald-700' : tone.change}`}>{metric.change}</span>
        <span className="text-slate-400">{metric.note}</span>
      </div>
    </article>
  )
}
