export default function LoadingState() {
  return (
    <div className="animate-pulse space-y-6" aria-label="Loading dashboard" role="status">
      <span className="sr-only">Loading dashboard data</span>
      <div className="h-8 w-52 rounded-lg bg-slate-200" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[1, 2, 3, 4].map((item) => <div key={item} className="h-32 rounded-xl border border-slate-200 bg-white p-5"><div className="h-3 w-28 rounded bg-slate-100" /><div className="mt-5 h-8 w-16 rounded bg-slate-100" /><div className="mt-4 h-3 w-24 rounded bg-slate-100" /></div>)}</div>
      <div className="h-80 rounded-xl border border-slate-200 bg-white" />
    </div>
  )
}
