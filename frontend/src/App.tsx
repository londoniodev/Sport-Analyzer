import { useState } from 'react'
import {
  TrendingUp,
  Activity,
  LayoutDashboard,
  Calendar,
  Users,
  Globe2
} from 'lucide-react'

import DashboardView from './components/DashboardView'
import PredictionsView from './components/PredictionsView'
import PlayerBrowserView from './components/PlayerBrowserView'
import RushbetView from './components/RushbetView'
import WorldCupView from './components/WorldCupView'

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] flex flex-col md:flex-row font-sans selection:bg-violet-500/30">
      {/* Sidebar */}
      <aside className="w-full md:w-72 bg-[#0f0f11]/95 backdrop-blur-xl border-b md:border-b-0 md:border-r border-zinc-800/50 p-6 flex flex-col gap-8 shadow-2xl z-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-violet-600/20 to-fuchsia-600/20 rounded-2xl border border-violet-500/30 text-violet-400 shadow-[0_0_15px_rgba(139,92,246,0.15)]">
            <Activity className="w-7 h-7" />
          </div>
          <div>
            <h1 className="font-extrabold text-xl leading-tight tracking-tight bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">Sport Analyzer</h1>
            <p className="text-xs text-zinc-500 font-medium tracking-wide uppercase mt-0.5">Predictive Engine</p>
          </div>
        </div>

        <div className="h-px bg-gradient-to-r from-zinc-800/0 via-zinc-800 to-zinc-800/0" />

        {/* Navigation */}
        <nav className="flex flex-col gap-2 flex-grow">
          <span className="text-[11px] tracking-widest text-zinc-500 font-bold uppercase mb-2">Navegación</span>
          
          {[
            { id: 'dashboard', icon: LayoutDashboard, label: 'Panel de Control' },
            { id: 'predictions', icon: Calendar, label: 'Predicciones' },
            { id: 'players', icon: Users, label: 'Explorador de Jugadores' },
            { id: 'rushbet', icon: TrendingUp, label: 'Eventos Rushbet' },
            { id: 'worldcup', icon: Globe2, label: 'Mundial 2026' }
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                activeTab === item.id
                  ? 'bg-gradient-to-r from-violet-600/10 to-transparent border-l-2 border-violet-500 text-violet-300 shadow-[inset_1px_0_0_rgba(139,92,246,0.5)]'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b] border-l-2 border-transparent'
              }`}
            >
              <item.icon className={`w-4 h-4 ${activeTab === item.id ? 'text-violet-400' : 'text-zinc-500'}`} />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="h-px bg-gradient-to-r from-zinc-800/0 via-zinc-800 to-zinc-800/0 mt-auto" />
        <div className="text-[10px] text-zinc-600 text-center font-mono py-1">v2.0.0 Stable</div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-grow p-6 md:p-10 overflow-y-auto max-w-7xl w-full mx-auto">
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'predictions' && <PredictionsView />}
        {activeTab === 'players' && <PlayerBrowserView />}
        {activeTab === 'rushbet' && <RushbetView />}
        {activeTab === 'worldcup' && <WorldCupView />}
      </main>
    </div>
  )
}
