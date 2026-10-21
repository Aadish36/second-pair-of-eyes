import Icon from './Icon.jsx'
import MistakeTrendsChart from './MistakeTrendsChart.jsx'
import ReviewTable from './ReviewTable.jsx'
import StatCard from './StatCard.jsx'

function SectionHeading({ eyebrow, title, description, action }) {
  return (
    <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
      <div><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{eyebrow}</p><h2 className="mt-1.5 text-base font-semibold tracking-tight text-slate-900">{title}</h2>{description && <p className="mt-1 text-[11px] text-slate-500">{description}</p>}</div>
      {action}
    </div>
  )
}

export default function DashboardView({ reviews, summary, onSelectReview, onViewAll, query }) {
  const metrics = [
    { label: 'PR revisions reviewed', value: summary?.metrics?.pull_requests_reviewed ?? 0, change: 'Live', note: 'persisted review heads', icon: 'gitPull', tone: 'violet' },
    { label: 'Issues found', value: summary?.metrics?.issues_found ?? 0, change: 'Live', note: 'analyzed findings', icon: 'scan', tone: 'blue' },
    { label: 'Critical issues', value: summary?.metrics?.critical_issues ?? 0, change: 'Live', note: 'high severity', icon: 'alert', tone: 'rose' },
    { label: 'Resolved issues', value: summary?.metrics?.resolved_issues ?? '—', change: 'N/A', note: 'resolution tracking unavailable', icon: 'check', tone: 'green' },
  ]
  return (
    <div className="space-y-7">
      <section>
        <div className="mb-4 flex items-center justify-between">
          <div><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Team overview</p><h2 className="mt-1.5 text-base font-semibold tracking-tight text-slate-900">Review activity</h2></div>
          <button className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[10px] font-semibold text-slate-600 shadow-sm hover:bg-slate-50"><Icon name="clock" size={14} />Last 30 days<Icon name="down" size={13} /></button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{metrics.map((metric) => <StatCard key={metric.label} metric={metric} />)}</div>
      </section>

      <section>
        <SectionHeading eyebrow="Patterns over time" title="Mistake trends" description="Issues identified across your team's recent reviews" action={<button onClick={onViewAll} className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#28634f] hover:text-[#173f33]">View mistake history<Icon name="chevron" size={15} /></button>} />
        <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.025)] sm:p-5"><MistakeTrendsChart compact trends={summary?.trends || []} categories={summary?.categories || []} /></div>
      </section>

      <section>
        <SectionHeading eyebrow="Latest activity" title="Recent code reviews" description="The latest pull requests reviewed by your team" action={<button onClick={onViewAll} className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#28634f] hover:text-[#173f33]">View all reviews<Icon name="chevron" size={15} /></button>} />
        <div className="overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-[0_2px_8px_rgba(15,23,42,0.025)]"><ReviewTable reviews={reviews.slice(0, 4)} onSelect={onSelectReview} query={query} compact /></div>
      </section>
    </div>
  )
}
