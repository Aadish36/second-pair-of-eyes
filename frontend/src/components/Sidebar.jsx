import Icon from './Icon.jsx'

const navigation = [
  { label: 'Dashboard', icon: 'grid', key: 'dashboard' },
  { label: 'Pull Requests', icon: 'gitPull', key: 'pull-requests', count: '8' },
  { label: 'Code Reviews', icon: 'scan', key: 'code-reviews' },
  { label: 'Mistake History', icon: 'history', key: 'mistake-history' },
]

export default function Sidebar({ activePage, onNavigate, isOpen, onClose }) {
  return (
    <>
      {isOpen && <button className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden" aria-label="Close navigation" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-[264px] flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-[76px] items-center justify-between border-b border-slate-100 px-6">
          <a href="#dashboard" onClick={(event) => { event.preventDefault(); onNavigate('dashboard') }} className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-xl bg-[#193d35] text-sm font-bold text-white">2e</span>
            <span className="text-[14px] font-semibold tracking-tight text-slate-900">Second Pair <span className="text-slate-400">of Eyes</span></span>
          </a>
          <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden" onClick={onClose} aria-label="Close navigation"><Icon name="close" size={18} /></button>
        </div>

        <div className="px-4 pt-7">
          <p className="px-3 pb-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Workspace</p>
          <nav className="space-y-1" aria-label="Main navigation">
            {navigation.map((item) => {
              const active = activePage === item.key || (activePage === 'review-details' && item.key === 'code-reviews')
              return (
                <button key={item.key} onClick={() => onNavigate(item.key)} className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13px] font-medium transition ${active ? 'bg-[#edf4f0] text-[#1d5b49]' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}>
                  <Icon name={item.icon} size={18} className={active ? 'text-[#28725a]' : 'text-slate-400 group-hover:text-slate-600'} />
                  <span className="flex-1">{item.label}</span>
                  {item.count && <span className={`rounded-md px-2 py-0.5 text-[10px] font-semibold ${active ? 'bg-white text-[#28725a]' : 'bg-slate-100 text-slate-500'}`}>{item.count}</span>}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="mt-9 px-4">
          <p className="px-3 pb-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Preferences</p>
          <button onClick={() => onNavigate('settings')} className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-[13px] font-medium transition ${activePage === 'settings' ? 'bg-[#edf4f0] text-[#1d5b49]' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}>
            <Icon name="settings" size={18} className="text-slate-400 group-hover:text-slate-600" />
            Settings
          </button>
        </div>

        <div className="mt-auto p-4">
          <div className="rounded-xl border border-[#e5ebe7] bg-[#f6f8f6] p-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#315f4e]"><Icon name="spark" size={15} /> Review mentor</div>
            <p className="mt-2 text-[11px] leading-5 text-slate-500">Mock workspace data is enabled. Connect integrations when you are ready.</p>
            <div className="mt-3 flex items-center gap-2 text-[10px] font-medium text-slate-500"><span className="size-1.5 rounded-full bg-amber-400" /> Demo mode</div>
          </div>
          <button className="mt-4 flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left hover:bg-slate-50">
            <span className="grid size-8 place-items-center rounded-full bg-[#e6ebe8] text-[10px] font-bold text-[#3e6052]">JD</span>
            <span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold text-slate-800">Jordan Davis</span><span className="block truncate text-[10px] text-slate-400">Engineering team</span></span>
            <Icon name="dots" size={18} className="text-slate-400" />
          </button>
        </div>
      </aside>
    </>
  )
}
