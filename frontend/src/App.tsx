import { useState, useEffect } from 'react'
import {
  TrendingUp,
  Activity,
  Award,
  Zap,
  LayoutDashboard,
  Calendar,
  Layers,
  Search,
  ChevronRight,
  Sliders,
  DollarSign
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card'
import { Badge } from './components/ui/badge'
import { Button } from './components/ui/button'

interface Match {
  id: string
  homeTeam: string
  awayTeam: string
  homeElo: number
  awayElo: number
  poissonHomeWin: number
  poissonDraw: number
  poissonAwayWin: number
  recommendedBet: string
  valueOdds: number
  realOdds: number
  edge: number
}

export default function App() {
  const [selectedSport, setSelectedSport] = useState('Fútbol')
  const [activeTab, setActiveTab] = useState('dashboard')
  const [searchQuery, setSearchQuery] = useState('')
  const [matches, setMatches] = useState<Match[]>([])

  // Fetch matches dynamically from FastAPI via Nginx proxy
  useEffect(() => {
    const fetchMatches = async () => {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_URL || ''
        const res = await fetch(`${apiBaseUrl}/api/matches?sport=${encodeURIComponent(selectedSport)}`)
        if (res.ok) {
          const data = await res.json()
          setMatches(data)
        }
      } catch (err) {
        console.error("Error fetching matches:", err)
      }
    }
    fetchMatches()
  }, [selectedSport])

  const filteredMatches = matches.filter(
    (match) =>
      match.homeTeam.toLowerCase().includes(searchQuery.toLowerCase()) ||
      match.awayTeam.toLowerCase().includes(searchQuery.toLowerCase())
  )

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

        {/* Sport Selector */}
        <div className="flex flex-col gap-2.5">
          <label className="text-[11px] tracking-widest text-zinc-500 font-bold uppercase">Deporte Activo</label>
          <div className="relative group">
            <select
              value={selectedSport}
              onChange={(e) => setSelectedSport(e.target.value)}
              className="w-full appearance-none py-3 px-4 bg-[#18181b] hover:bg-[#1f1f23] border border-zinc-800/80 rounded-xl text-sm font-medium text-zinc-200 focus:outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all cursor-pointer shadow-sm"
            >
              <option>Fútbol</option>
              <option>Baloncesto</option>
              <option>Tenis</option>
            </select>
            <ChevronRight className="absolute right-4 top-3.5 w-4 h-4 text-zinc-500 pointer-events-none group-hover:text-violet-400 transition-colors rotate-90" />
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-2 flex-grow">
          <span className="text-[11px] tracking-widest text-zinc-500 font-bold uppercase mb-2">Navegación</span>
          
          {[
            { id: 'dashboard', icon: LayoutDashboard, label: 'Panel de Control' },
            { id: 'predictions', icon: Calendar, label: 'Predicciones' },
            { id: 'valuebets', icon: TrendingUp, label: 'Value Bets' }
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
        {/* Top Header */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
          <div>
            <h2 className="text-3xl font-extrabold tracking-tight mb-2 bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
              Análisis de {selectedSport}
            </h2>
            <p className="text-sm text-zinc-400 font-medium">Modelos ELO y Poisson aplicados en tiempo real</p>
          </div>

          <div className="relative w-full md:w-80 group">
            <Search className="absolute left-4 top-3 w-4 h-4 text-zinc-500 group-focus-within:text-violet-400 transition-colors" />
            <input
              type="text"
              placeholder="Buscar equipo o evento..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#121214] border border-zinc-800 rounded-xl pl-11 pr-4 py-2.5 text-sm font-medium text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all shadow-sm hover:border-zinc-700"
            />
          </div>
        </header>

        {/* Dynamic Content */}
        {activeTab === 'dashboard' && (
          <div className="flex flex-col gap-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Feature Cards Grid */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="border-violet-500/10 bg-gradient-to-b from-[#18181b]/80 to-[#121214]/80 shadow-[0_4px_20px_rgba(139,92,246,0.03)] hover:border-violet-500/30 transition-all duration-300">
                <CardHeader className="pb-4">
                  <div className="p-3.5 bg-violet-500/10 text-violet-400 rounded-xl w-fit mb-4 border border-violet-500/20">
                    <Layers className="w-5 h-5" />
                  </div>
                  <CardTitle className="text-lg">Modelos Poisson</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="leading-relaxed">
                    Cálculo preciso de goles mediante distribuciones de probabilidad basadas en promedios ofensivos y defensivos.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="border-emerald-500/10 bg-gradient-to-b from-[#18181b]/80 to-[#121214]/80 shadow-[0_4px_20px_rgba(16,185,129,0.03)] hover:border-emerald-500/30 transition-all duration-300">
                <CardHeader className="pb-4">
                  <div className="p-3.5 bg-emerald-500/10 text-emerald-400 rounded-xl w-fit mb-4 border border-emerald-500/20">
                    <Award className="w-5 h-5" />
                  </div>
                  <CardTitle className="text-lg">Rating ELO</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="leading-relaxed">
                    Clasificación de fuerza relativa dinámica basada en el historial de rendimiento contra oponentes directos.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="border-amber-500/10 bg-gradient-to-b from-[#18181b]/80 to-[#121214]/80 shadow-[0_4px_20px_rgba(245,158,11,0.03)] hover:border-amber-500/30 transition-all duration-300">
                <CardHeader className="pb-4">
                  <div className="p-3.5 bg-amber-500/10 text-amber-400 rounded-xl w-fit mb-4 border border-amber-500/20">
                    <Zap className="w-5 h-5" />
                  </div>
                  <CardTitle className="text-lg">Value Bets</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="leading-relaxed">
                    Detección automática de cuotas sobrevaloradas en el mercado que presentan valor esperado positivo (+EV).
                  </CardDescription>
                </CardContent>
              </Card>
            </section>

            {/* Quick Overview Predictions */}
            <section>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-bold text-xl tracking-tight">Predicciones Destacadas</h3>
                  <p className="text-sm text-zinc-400 mt-1">Próximos encuentros con mayor probabilidad de acierto</p>
                </div>
                <Button variant="ghost" onClick={() => setActiveTab('predictions')} className="text-violet-400 hover:text-violet-300">
                  Ver todas <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {filteredMatches.slice(0, 2).map((match) => (
                  <Card key={match.id} className="hover:border-zinc-700 transition-colors bg-[#121214] shadow-md group">
                    <CardContent className="p-6">
                      <div className="flex justify-between items-center mb-5">
                        <div className="flex flex-col gap-1">
                          <span className="font-bold text-base tracking-tight">{match.homeTeam}</span>
                          <span className="text-xs text-zinc-500 font-mono">ELO: {match.homeElo}</span>
                        </div>
                        <Badge variant="outline" className="px-3 py-1 font-mono tracking-widest text-[10px] bg-[#18181b]">VS</Badge>
                        <div className="flex flex-col items-end gap-1">
                          <span className="font-bold text-base tracking-tight">{match.awayTeam}</span>
                          <span className="text-xs text-zinc-500 font-mono">ELO: {match.awayElo}</span>
                        </div>
                      </div>

                      <div className="h-px bg-zinc-800/80 mb-5 w-full" />

                      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-sm">
                        <div className="flex gap-3 text-xs font-mono text-zinc-400 bg-[#18181b] px-3 py-1.5 rounded-lg border border-zinc-800">
                          <span className="text-zinc-300">L: {match.poissonHomeWin}%</span>
                          <span className="text-zinc-500">•</span>
                          <span className="text-zinc-300">E: {match.poissonDraw}%</span>
                          <span className="text-zinc-500">•</span>
                          <span className="text-zinc-300">V: {match.poissonAwayWin}%</span>
                        </div>
                        <Badge variant="default" className="shadow-lg shadow-violet-500/20">
                          {match.recommendedBet}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h3 className="font-bold text-xl tracking-tight mb-1">Predicciones Estadísticas</h3>
              <p className="text-sm text-zinc-400">Probabilidad calculada por modelos de distribución Poisson</p>
            </div>

            <div className="grid grid-cols-1 gap-5">
              {filteredMatches.map((match) => (
                <Card key={match.id} className="overflow-hidden hover:border-zinc-700 transition-colors">
                  <div className="flex flex-col lg:flex-row">
                    <CardContent className="p-6 flex-grow flex flex-col md:flex-row items-center gap-8">
                      {/* Teams Info */}
                      <div className="w-full md:w-1/3 flex items-center justify-between gap-4">
                        <div className="text-left w-2/5">
                          <h4 className="font-bold text-[15px] truncate">{match.homeTeam}</h4>
                          <p className="text-[11px] text-zinc-500 font-mono mt-1">ELO: {match.homeElo}</p>
                        </div>
                        <Badge variant="outline" className="px-2 py-0.5 text-[10px]">VS</Badge>
                        <div className="text-right w-2/5">
                          <h4 className="font-bold text-[15px] truncate">{match.awayTeam}</h4>
                          <p className="text-[11px] text-zinc-500 font-mono mt-1">ELO: {match.awayElo}</p>
                        </div>
                      </div>

                      {/* Probability Bar */}
                      <div className="w-full md:w-2/3 flex flex-col gap-2">
                        <div className="flex justify-between text-[11px] font-mono font-medium text-zinc-400 px-1">
                          <span>Local: <span className="text-zinc-200">{match.poissonHomeWin}%</span></span>
                          <span>Empate: <span className="text-zinc-200">{match.poissonDraw}%</span></span>
                          <span>Visita: <span className="text-zinc-200">{match.poissonAwayWin}%</span></span>
                        </div>
                        <div className="h-2.5 w-full bg-[#18181b] rounded-full overflow-hidden flex border border-zinc-800 shadow-inner">
                          <div className="bg-violet-500" style={{ width: `${match.poissonHomeWin}%` }} />
                          <div className="bg-zinc-600" style={{ width: `${match.poissonDraw}%` }} />
                          <div className="bg-emerald-500" style={{ width: `${match.poissonAwayWin}%` }} />
                        </div>
                      </div>
                    </CardContent>

                    <div className="bg-[#18181b] p-6 lg:w-56 flex flex-row lg:flex-col items-center lg:items-end justify-between lg:justify-center border-t lg:border-t-0 lg:border-l border-zinc-800 gap-3">
                      <div className="text-left lg:text-right">
                        <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold mb-1">Mejor Opción</p>
                        <p className="font-bold text-sm text-violet-400">{match.recommendedBet}</p>
                      </div>
                      <Badge variant="secondary" className="border border-zinc-700/50 flex gap-1.5 py-1">
                        <Sliders className="w-3 h-3 text-zinc-400" />
                        Cuota: {match.realOdds.toFixed(2)}
                      </Badge>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'valuebets' && (
          <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h3 className="font-bold text-xl tracking-tight mb-1">Oportunidades de Value Betting</h3>
              <p className="text-sm text-zinc-400">Cuotas de mercado con margen esperado positivo (+EV)</p>
            </div>

            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[#18181b] border-b border-zinc-800 text-[11px] font-bold text-zinc-400 uppercase tracking-widest">
                      <th className="py-4 px-6 w-1/3">Encuentro</th>
                      <th className="py-4 px-6 text-center">Pronóstico</th>
                      <th className="py-4 px-6 text-center">Cuota Justa</th>
                      <th className="py-4 px-6 text-center">Cuota Real</th>
                      <th className="py-4 px-6 text-center">Edge</th>
                      <th className="py-4 px-6 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50 text-sm">
                    {filteredMatches.map((match) => (
                      <tr key={match.id} className="hover:bg-[#18181b]/50 transition-colors group">
                        <td className="py-5 px-6 font-semibold tracking-tight">
                          {match.homeTeam} <span className="text-zinc-600 font-normal mx-1">vs</span> {match.awayTeam}
                        </td>
                        <td className="py-5 px-6 text-center">
                          <Badge variant="outline" className="bg-[#121214] font-medium border-zinc-700">{match.recommendedBet}</Badge>
                        </td>
                        <td className="py-5 px-6 text-center font-mono text-zinc-400">{match.valueOdds.toFixed(2)}</td>
                        <td className="py-5 px-6 text-center font-mono text-zinc-100 font-bold">{match.realOdds.toFixed(2)}</td>
                        <td className="py-5 px-6 text-center">
                          <Badge variant="success" className="font-mono text-xs shadow-sm">+{match.edge}%</Badge>
                        </td>
                        <td className="py-5 px-6 text-right">
                          <Button size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
                            <DollarSign className="w-3.5 h-3.5 mr-1" />
                            Apostar
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}
