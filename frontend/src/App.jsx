import { useEffect, useState } from 'react'
import DashboardView from './components/DashboardView.jsx'
import Icon from './components/Icon.jsx'
import LoadingState from './components/LoadingState.jsx'
import ReviewDetails from './components/ReviewDetails.jsx'
import Sidebar from './components/Sidebar.jsx'
import { MistakeHistoryPage, ReviewListPage, SettingsPage } from './components/SectionPages.jsx'
import { fetchDashboard, loginDashboard, toDashboardReview } from './api.js'

const pageNames = { dashboard: 'Dashboard', 'pull-requests': 'Pull Requests', 'code-reviews': 'Code Reviews', 'mistake-history': 'Mistake History', settings: 'Settings', 'review-details': 'Review details' }

function PageContent({ page, reviews, summary, selectedReview, query, onSelectReview, onNavigate }) {
  if (page === 'review-details') return <ReviewDetails review={selectedReview} onBack={() => onNavigate('code-reviews')} />
  if (page === 'pull-requests') return <ReviewListPage title="Pull Requests" description="GitHub pull requests reviewed by this service." reviews={reviews} onSelectReview={onSelectReview} query={query} />
  if (page === 'code-reviews') return <ReviewListPage title="Code Reviews" description="Persisted findings, explanations, and suggested fixes." reviews={reviews} onSelectReview={onSelectReview} query={query} />
  if (page === 'mistake-history') return <MistakeHistoryPage summary={summary} />
  if (page === 'settings') return <SettingsPage />
  return <DashboardView reviews={reviews} summary={summary} onSelectReview={onSelectReview} onViewAll={() => onNavigate('code-reviews')} query={query} />
}

function App() {
  const [page, setPage] = useState('dashboard')
  const [selectedReview, setSelectedReview] = useState(null)
  const [query, setQuery] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState(null)
  const [loadError, setLoadError] = useState('')
  const [authRequired, setAuthRequired] = useState(false)
  const [loginToken, setLoginToken] = useState('')
  const [loginBusy, setLoginBusy] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    fetchDashboard(controller.signal)
      .then((data) => { setSummary(data); setLoadError('') })
      .catch((error) => { if (error.name !== 'AbortError') { setLoadError(error.message); setAuthRequired(error.status === 401) } })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [])

  const reviews = (summary?.items || []).map(toDashboardReview)
  async function handleLogin(event) {
    event.preventDefault()
    setLoginBusy(true)
    setLoadError('')
    try {
      await loginDashboard(loginToken)
      const data = await fetchDashboard()
      setSummary(data)
      setAuthRequired(false)
      setLoginToken('')
    } catch (error) {
      setLoadError(error.message)
      setAuthRequired(error.status === 401 || authRequired)
    } finally { setLoginBusy(false) }
  }
  function navigate(nextPage) { setPage(nextPage); setSidebarOpen(false); setQuery('') }
  function handleSelectReview(review) { setSelectedReview(review); setPage('review-details') }

  return (
    <div className="min-h-screen bg-[#f7f8f7] text-slate-900">
      <Sidebar activePage={page} onNavigate={navigate} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="min-h-screen lg:pl-[264px]">
        <header className="sticky top-0 z-30 flex h-[68px] items-center justify-between gap-4 border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur sm:px-7 lg:px-9">
          <div className="flex min-w-0 items-center gap-3"><button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Icon name="menu" /></button><div className="hidden items-center gap-2 text-[11px] text-slate-400 sm:flex"><span>Workspace</span><Icon name="chevron" size={13} /></div><h1 className="truncate text-[13px] font-semibold text-slate-800">{pageNames[page]}</h1></div>
          <div className="flex items-center gap-2.5 sm:gap-4"><label className="hidden h-9 w-48 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 md:flex lg:w-64"><Icon name="search" size={15} className="shrink-0 text-slate-400" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search reviews..." className="w-full bg-transparent text-[11px] text-slate-700 outline-none placeholder:text-slate-400" aria-label="Search reviews" /><kbd className="rounded border border-slate-200 bg-white px-1 text-[9px] text-slate-400">Ctrl K</kbd></label><span className="hidden rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[9px] font-semibold text-emerald-700 sm:inline-flex">{summary?.source === 'postgresql' ? 'POSTGRESQL' : 'LIVE API'}</span></div>
        </header>
        <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-7 sm:py-8 lg:px-9">
          {authRequired && <form onSubmit={handleLogin} className="mx-auto mb-6 max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-sm font-semibold text-slate-900">Dashboard sign in</h2><p className="mt-1 text-xs text-slate-500">Enter the dashboard token configured for the backend.</p><input type="password" autoComplete="current-password" required value={loginToken} onChange={(event) => setLoginToken(event.target.value)} className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" aria-label="Dashboard token" />{loadError && <p role="alert" className="mt-2 text-xs text-rose-700">{loadError}</p>}<button disabled={loginBusy} className="mt-3 rounded-lg bg-[#224f41] px-4 py-2 text-xs font-semibold text-white disabled:opacity-60">{loginBusy ? 'Signing in…' : 'Sign in'}</button></form>}
          {page === 'dashboard' && <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-[11px] font-medium text-slate-400">{new Date().toLocaleDateString()}</p><h1 className="mt-1 text-[25px] font-semibold tracking-[-0.045em] text-slate-900 sm:text-[28px]">Code review overview <span aria-hidden="true">✦</span></h1><p className="mt-1 text-xs text-slate-500">Persisted GitHub pull request reviews and findings.</p></div><button onClick={() => navigate('pull-requests')} className="inline-flex w-fit items-center gap-2 rounded-lg bg-[#224f41] px-4 py-2.5 text-[11px] font-semibold text-white shadow-sm transition hover:bg-[#183d32]"><Icon name="gitPull" size={15} />View pull requests</button></div>}
          {loadError && <div role="alert" className="mb-5 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">Could not load dashboard data: {loadError}. Check the backend, PostgreSQL, and dashboard token configuration.</div>}
          {loading ? <LoadingState /> : <PageContent page={page} reviews={reviews} summary={summary} selectedReview={selectedReview} query={query} onSelectReview={handleSelectReview} onNavigate={navigate} />}
          <footer className="mt-10 flex flex-col gap-2 border-t border-slate-200/80 pt-5 text-[10px] text-slate-400 sm:flex-row sm:items-center sm:justify-between"><span>Second Pair of Eyes <span className="px-1">·</span> Context-aware code review mentor</span><span>Dashboard reads persisted GitHub reviews from the API.</span></footer>
        </main>
      </div>
    </div>
  )
}

export default App
