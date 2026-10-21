import Icon from './Icon.jsx'

const severityStyle = {
  Critical: 'bg-rose-50 text-rose-700 ring-rose-600/15',
  High: 'bg-orange-50 text-orange-700 ring-orange-600/15',
  Medium: 'bg-amber-50 text-amber-700 ring-amber-600/15',
  Low: 'bg-sky-50 text-sky-700 ring-sky-600/15',
}

export default function ReviewDetails({ review, onBack }) {
  const findings = review.findings || []
  const historicalExamples = findings.flatMap((finding) => (finding.history || []).map((example) => ({ ...example, findingMessage: finding.message })))
  return (
    <div className="mx-auto max-w-5xl">
      <button onClick={onBack} className="mb-5 inline-flex items-center gap-2 text-xs font-semibold text-slate-500 transition hover:text-[#25644f]"><span className="rotate-180"><Icon name="chevron" size={16} /></span>Back to code reviews</button>
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2 text-[10px] font-medium text-slate-400"><span>{review.repository}</span><span>·</span><span>#{review.number}</span><span>·</span><span>{review.branch}</span></div>
          <h1 className="max-w-3xl text-2xl font-semibold tracking-[-0.035em] text-slate-900 sm:text-[30px]">{review.title}</h1>
          <p className="mt-2 text-xs text-slate-500">Head <span className="font-mono text-slate-700">{review.branch}</span> · updated {review.updated}</p>
        </div>
        <span className={`inline-flex w-fit items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-semibold ring-1 ring-inset ${severityStyle[review.severity] ?? severityStyle.Low}`}><Icon name="alert" size={13} />{review.severity} severity</span>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-5">
          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-5 py-4">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-800"><Icon name="code" size={16} className="text-slate-400" />{review.file}</div>
              <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-[10px] text-slate-500">Line {review.line}</span>
            </div>
            {review.code ? <div className="overflow-x-auto bg-[#101a1a] p-5"><pre className="font-mono text-[11px] leading-6 text-[#d8e1dd]"><code>{review.code}</code></pre></div> : <div className="px-5 py-8 text-center text-xs text-slate-400">Source excerpts are not stored with persisted reviews.</div>}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            {findings.length ? findings.map((finding, index) => <article key={`${finding.path}-${finding.line}-${index}`} className={index ? 'mt-6 border-t border-slate-100 pt-5' : ''}>
              <div className="flex items-start gap-3"><span className="grid size-9 shrink-0 place-items-center rounded-lg bg-rose-50 text-rose-600"><Icon name="alert" size={17} /></span><div><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-rose-600">{finding.severity} issue · {finding.path || 'file unavailable'} · line {finding.line ?? '—'}</p><h2 className="mt-1 text-[16px] font-semibold leading-6 tracking-tight text-slate-900">{finding.message}</h2></div></div>
              <div className="mt-5 border-t border-slate-100 pt-5"><h3 className="flex items-center gap-2 text-xs font-semibold text-slate-800"><Icon name="spark" size={15} className="text-[#518c72]" />Why this matters</h3><p className="mt-2 text-[13px] leading-6 text-slate-600">{finding.explanation || 'No explanation was recorded.'}</p>{finding.risk && <p className="mt-2 text-[12px] leading-5 text-slate-500">Risk: {finding.risk}</p>}</div>
              <div className="mt-5 rounded-lg border border-emerald-100 bg-emerald-50/60 p-4"><h3 className="flex items-center gap-2 text-xs font-semibold text-emerald-900"><Icon name="check" size={15} />Suggested fix</h3><p className="mt-2 text-[12px] leading-5 text-emerald-950/75">{finding.fix || 'No fix guidance was recorded.'}</p></div>
            </article>) : <p className="text-sm text-slate-500">No findings were stored for this pull request revision.</p>}
          </section>
        </div>

        <aside className="space-y-4">
          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-xs font-semibold text-slate-800">Review summary</h2>
            <div className="mt-4 space-y-3 text-[11px]">
              <div className="flex justify-between"><span className="text-slate-500">Status</span><span className="font-semibold text-slate-700">{review.status}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Findings</span><span className="font-semibold text-slate-700">{review.issueCount} {review.issueCount === 1 ? 'issue' : 'issues'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Author</span><span className="font-semibold text-slate-700">{review.author}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Last activity</span><span className="font-semibold text-slate-700">{review.updated}</span></div>
            </div>
            <a href={review.githubUrl} target="_blank" rel="noreferrer" className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 py-2.5 text-[11px] font-semibold text-slate-600 transition hover:bg-slate-50"><Icon name="arrow" size={14} />Open pull request</a>
          </section>
          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-xs font-semibold text-slate-800">Historical context</h2>
            <div className="mt-4 rounded-lg bg-slate-50 p-3"><span className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Verified historical examples</span>{historicalExamples.length ? historicalExamples.map((example, index) => <div key={`${example.commit_sha}-${index}`} className="mt-3 border-t border-slate-200 pt-3"><a href={example.url || '#'} target="_blank" rel="noreferrer" className="font-mono text-[10px] font-semibold text-emerald-800">{example.short_sha}</a><p className="mt-1 text-[11px] text-slate-700">{example.subject}</p><p className="mt-1 text-[10px] leading-4 text-slate-500">Related finding: {example.findingMessage}</p><p className="mt-1 text-[10px] leading-4 text-slate-500">{example.evidence}</p></div>) : <p className="mt-2 text-[11px] leading-5 text-slate-500">{review.history_message || 'No verified historical example was recorded.'}</p>}</div>
          </section>
        </aside>
      </div>
    </div>
  )
}
