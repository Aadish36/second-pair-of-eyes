import Icon from './Icon.jsx'

const statusStyles = {
  'Needs attention': 'bg-rose-50 text-rose-700 ring-rose-600/10',
  'In review': 'bg-amber-50 text-amber-700 ring-amber-600/10',
  Approved: 'bg-emerald-50 text-emerald-700 ring-emerald-600/10',
  Resolved: 'bg-slate-100 text-slate-600 ring-slate-500/10',
  Reviewed: 'bg-emerald-50 text-emerald-700 ring-emerald-600/10',
}

function EmptyState({ query }) {
  return (
    <div className="flex flex-col items-center px-6 py-12 text-center">
      <span className="grid size-11 place-items-center rounded-full bg-slate-100 text-slate-400"><Icon name="search" /></span>
      <h3 className="mt-4 text-sm font-semibold text-slate-800">No reviews found</h3>
      <p className="mt-1 max-w-xs text-xs leading-5 text-slate-500">{query ? `No pull requests match “${query}”. Try a different search.` : 'Reviews will appear here when the workspace has data.'}</p>
    </div>
  )
}

export default function ReviewTable({ reviews, onSelect, query = '', compact = false }) {
  const filtered = reviews.filter((review) => `${review.title} ${review.author} ${review.repository}`.toLowerCase().includes(query.toLowerCase()))
  if (!filtered.length) return <EmptyState query={query} />

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[680px] border-collapse text-left">
        <thead>
          <tr className="border-y border-slate-100 bg-slate-50/70 text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-400">
            <th className="px-5 py-3 font-semibold">Pull request</th>
            <th className="px-4 py-3 font-semibold">Author</th>
            <th className="px-4 py-3 font-semibold">Status</th>
            <th className="px-4 py-3 text-right font-semibold">Issues</th>
            {!compact && <th className="px-5 py-3 text-right font-semibold">Updated</th>}
            <th className="w-9 px-3 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {filtered.map((review) => (
            <tr key={review.id} className="group cursor-pointer transition hover:bg-slate-50/80" onClick={() => onSelect(review)} onKeyDown={(event) => { if (event.key === 'Enter') onSelect(review) }} tabIndex={0}>
              <td className="px-5 py-4">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-500"><Icon name="gitPull" size={15} /></span>
                  <span className="min-w-0"><span className="block max-w-[260px] truncate text-[12px] font-semibold text-slate-800 group-hover:text-[#25644f]">{review.title}</span><span className="mt-1 block text-[10px] text-slate-400">#{review.number} · {review.repository}</span></span>
                </div>
              </td>
              <td className="px-4 py-4"><span className="flex items-center gap-2 whitespace-nowrap text-[11px] font-medium text-slate-600"><span className="grid size-6 place-items-center rounded-full bg-[#e7eeea] text-[9px] font-bold text-[#3d6352]">{review.initials}</span>{review.author}</span></td>
              <td className="px-4 py-4"><span className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-[10px] font-medium ring-1 ring-inset ${statusStyles[review.status] ?? statusStyles['In review']}`}>{review.status}</span></td>
              <td className="px-4 py-4 text-right"><span className={`inline-flex min-w-7 justify-center rounded-md px-2 py-1 text-[11px] font-semibold ${review.issueCount > 0 ? review.severity === 'Critical' ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600' : 'text-slate-400'}`}>{review.issueCount}</span></td>
              {!compact && <td className="px-5 py-4 text-right text-[10px] text-slate-400">{review.updated}</td>}
              <td className="px-3 py-4"><Icon name="chevron" size={16} className="text-slate-300 group-hover:text-slate-500" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
