import Icon from './Icon.jsx'
import MistakeTrendsChart from './MistakeTrendsChart.jsx'
import ReviewTable from './ReviewTable.jsx'

export function ReviewListPage({ title, description, reviews, onSelectReview, query, filter }) {
  const rows = filter ? reviews.filter((review) => filter(review)) : reviews
  return (
    <div>
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Workspace</p><h1 className="mt-1.5 text-2xl font-semibold tracking-[-0.04em] text-slate-900">{title}</h1><p className="mt-1.5 text-xs text-slate-500">{description}</p></div>
        <span className="w-fit rounded-lg bg-white px-3 py-2 text-[10px] font-medium text-slate-500 ring-1 ring-slate-200">{rows.length} pull requests</span>
      </div>
      <div className="overflow-hidden rounded-xl border border-slate-200/80 bg-white"><ReviewTable reviews={rows} onSelect={onSelectReview} query={query} /></div>
    </div>
  )
}

export function MistakeHistoryPage({ summary }) {
  const categories = summary?.categories || []
  return (
    <div className="space-y-6">
      <div><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Learning insights</p><h1 className="mt-1.5 text-2xl font-semibold tracking-[-0.04em] text-slate-900">Mistake history</h1><p className="mt-1.5 text-xs text-slate-500">Explore recurring issue categories and how they change over time.</p></div>
      <section className="rounded-xl border border-slate-200/80 bg-white p-5 sm:p-6"><div className="mb-5"><h2 className="text-sm font-semibold text-slate-900">Issue patterns by week</h2><p className="mt-1 text-[11px] text-slate-500">Finding counts grouped by stored review date and category</p></div><MistakeTrendsChart trends={summary?.trends || []} categories={categories} /></section>
      <section className="rounded-xl border border-slate-200/80 bg-white p-5 sm:p-6"><h2 className="text-sm font-semibold text-slate-900">Recurring learning areas</h2><div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{categories.map((item) => <article key={item.label} className="rounded-lg border border-slate-100 p-4"><span className="inline-flex rounded-md bg-violet-50 px-2 py-1 text-[10px] font-semibold text-violet-700">{item.label}</span><p className="mt-3 text-[11px] leading-5 text-slate-500">Derived from stored issue types and messages.</p><p className="mt-3 text-lg font-semibold tracking-tight text-slate-800">{item.count}<span className="ml-1 text-[10px] font-normal text-slate-400">findings</span></p></article>)}</div></section>
    </div>
  )
}

export function SettingsPage() {
  const settings = [
    ['Review notifications', 'Receive a notification when a new review is ready.', true],
    ['Critical issue alerts', 'Highlight critical findings at the top of each review.', true],
    ['Weekly learning summary', 'Send a weekly summary of recurring team patterns.', false],
  ]
  return (
    <div className="max-w-3xl">
      <div className="mb-6"><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Workspace preferences</p><h1 className="mt-1.5 text-2xl font-semibold tracking-[-0.04em] text-slate-900">Settings</h1><p className="mt-1.5 text-xs text-slate-500">Manage how the review workspace is presented.</p></div>
      <section className="overflow-hidden rounded-xl border border-slate-200/80 bg-white">
        <div className="border-b border-slate-100 px-5 py-4"><h2 className="text-xs font-semibold text-slate-800">Notifications</h2><p className="mt-1 text-[10px] text-slate-500">These preferences are local demo controls only.</p></div>
        <div className="divide-y divide-slate-100">{settings.map(([title, detail, enabled]) => <label key={title} className="flex cursor-pointer items-center justify-between gap-4 px-5 py-4"><span><span className="block text-xs font-semibold text-slate-700">{title}</span><span className="mt-1 block text-[10px] text-slate-500">{detail}</span></span><input type="checkbox" defaultChecked={enabled} className="size-4 accent-[#2b7058]" aria-label={title} /></label>)}</div>
      </section>
      <div className="mt-5 flex gap-3 rounded-xl border border-amber-100 bg-amber-50/70 p-4"><Icon name="alert" size={16} className="mt-0.5 shrink-0 text-amber-700" /><p className="text-[11px] leading-5 text-amber-900">These notification preferences are browser-local demo controls. Configure GitHub, database, and AI credentials in the backend environment.</p></div>
    </div>
  )
}
