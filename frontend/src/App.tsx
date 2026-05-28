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

  // Fetch matches dynamically from FastAPI
  useEffect(() => {
    const fetchMatches = async () => {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
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
    <div className="min-h-screen bg-[#09090b] text-[#fafafa] flex flex-col md:flex-row">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-[#0f0f11]/90 backdrop-blur-md border-b md:border-b-0 md:border-r border-[#27272a] p-6 flex flex-col gap-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-violet-600/10 rounded-xl border border-violet-500/20 text-violet-400 accent-glow">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight tracking-tight">Sport Analyzer</h1>
            <p className="text-xs text-zinc-500">AI Predictive Engine</p>
          </div>
        </div>

        <div className="h-[1px] bg-zinc-800" />

        {/* Sport Selector */}
        <div className="flex flex-col gap-2">
          <label className="text-[10px] tracking-wider text-zinc-500 font-semibold uppercase">Deporte</label>
          <select
            value={selectedSport}
            onChange={(e) => setSelectedSport(e.target.value)}
            className="w-full py-2 px-3 bg-[#18181b] border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:border-violet-500 transition-colors"
          >
            <option>Fútbol</option>
            <option>Baloncesto</option>
            <option>Tenis</option>
          </select>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1.5 flex-grow">
          <span className="text-[10px] tracking-wider text-zinc-500 font-semibold uppercase mb-2">Navegación</span>
          
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'dashboard'
                ? 'bg-violet-600/10 border-l-2 border-violet-500 text-violet-400'
                : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            Panel de Control
          </button>

          <button
            onClick={() => setActiveTab('predictions')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'predictions'
                ? 'bg-violet-600/10 border-l-2 border-violet-500 text-violet-400'
                : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
            }`}
          >
            <Calendar className="w-4 h-4" />
            Predicciones
          </button>

          <button
            onClick={() => setActiveTab('valuebets')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'valuebets'
                ? 'bg-violet-600/10 border-l-2 border-violet-500 text-violet-400'
                : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            Value Bets
          </button>
        </nav>

        <div className="h-[1px] bg-zinc-800 mt-auto" />
        <div className="text-[10px] text-zinc-600 text-center font-mono py-2">v2.0.0 Stable</div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-grow p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
        {/* Top Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight">
              Análisis de {selectedSport}
            </h2>
            <p className="text-sm text-zinc-400">Modelos ELO y Poisson aplicados en tiempo real</p>
          </div>

          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Buscar equipo..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#121214] border border-zinc-800 rounded-lg pl-9 pr-4 py-2 text-sm text-zinc-300 placeholder-zinc-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-all"
            />
          </div>
        </header>

        {/* Dynamic Content */}
        {activeTab === 'dashboard' && (
          <div className="flex flex-col gap-8">
            {/* Feature Cards Grid */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass p-6 rounded-2xl relative overflow-hidden accent-glow">
                <div className="p-3 bg-violet-600/10 border border-violet-500/20 text-violet-400 rounded-xl w-fit mb-4">
                  <Layers className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-lg mb-2">Modelos Poisson</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  Cálculo preciso de goles mediante distribuciones de probabilidad basadas en promedios ofensivos y defensivos.
                </p>
              </div>

              <div className="glass p-6 rounded-2xl relative overflow-hidden accent-glow">
                <div className="p-3 bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 rounded-xl w-fit mb-4">
                  <Award className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-lg mb-2">Rating ELO</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  Clasificación de fuerza relativa dinámica basada en el historial de rendimiento contra oponentes directos.
                </p>
              </div>

              <div className="glass p-6 rounded-2xl relative overflow-hidden accent-glow">
                <div className="p-3 bg-amber-600/10 border border-amber-500/20 text-amber-400 rounded-xl w-fit mb-4">
                  <Zap className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-lg mb-2">Value Bets</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  Detección automática de cuotas sobrevaloradas en el mercado que presentan valor esperado positivo (+EV).
                </p>
              </div>
            </section>

            {/* Quick Overview Predictions */}
            <section className="glass rounded-2xl p-6 border border-[#27272a]">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-bold text-lg">Predicciones Destacadas</h3>
                  <p className="text-xs text-zinc-400">Próximos encuentros con mayor probabilidad de acierto</p>
                </div>
                <button
                  onClick={() => setActiveTab('predictions')}
                  className="flex items-center gap-1.5 text-xs text-violet-400 hover:text-violet-300 font-semibold transition-colors"
                >
                  Ver todas
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {filteredMatches.slice(0, 2).map((match) => (
                  <div
                    key={match.id}
                    className="p-5 bg-[#121214] border border-zinc-800 hover:border-zinc-700 rounded-xl transition-all flex flex-col gap-4"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex flex-col">
                        <span className="font-bold text-sm">{match.homeTeam}</span>
                        <span className="text-zinc-500 text-xs">ELO: {match.homeElo}</span>
                      </div>
                      <span className="text-xs font-mono text-zinc-600">VS</span>
                      <div className="flex flex-col items-end">
                        <span className="font-bold text-sm">{match.awayTeam}</span>
                        <span className="text-zinc-500 text-xs">ELO: {match.awayElo}</span>
                      </div>
                    </div>

                    <div className="h-[1px] bg-zinc-800/80" />

                    <div className="flex justify-between text-xs text-zinc-400">
                      <span>Prob: {match.poissonHomeWin}% L / {match.poissonDraw}% E / {match.poissonAwayWin}% V</span>
                      <span className="text-violet-400 font-semibold bg-violet-600/10 px-2 py-0.5 rounded">
                        Recomendado: {match.recommendedBet}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg">Predicciones Estadísticas</h3>
                <p className="text-xs text-zinc-400">Probabilidad calculada por modelos Poisson</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
              {filteredMatches.map((match) => (
                <div key={match.id} className="glass p-6 rounded-2xl flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  <div className="flex-grow flex flex-col md:flex-row items-center gap-6">
                    {/* Teams Info */}
                    <div className="w-full md:w-1/3 flex items-center justify-between md:justify-start gap-4">
                      <div className="text-left">
                        <h4 className="font-bold text-base">{match.homeTeam}</h4>
                        <p className="text-xs text-zinc-500 font-mono">ELO: {match.homeElo}</p>
                      </div>
                      <span className="text-xs font-mono px-2 py-1 bg-[#18181b] border border-zinc-800 rounded">VS</span>
                      <div className="text-right md:text-left">
                        <h4 className="font-bold text-base">{match.awayTeam}</h4>
                        <p className="text-xs text-zinc-500 font-mono">ELO: {match.awayElo}</p>
                      </div>
                    </div>

                    {/* Probability Bar */}
                    <div className="w-full md:w-2/3 flex flex-col gap-1.5">
                      <div className="flex justify-between text-[11px] font-mono text-zinc-400">
                        <span>L: {match.poissonHomeWin}%</span>
                        <span>E: {match.poissonDraw}%</span>
                        <span>V: {match.poissonAwayWin}%</span>
                      </div>
                      <div className="h-2.5 w-full bg-[#18181b] rounded-full overflow-hidden flex border border-zinc-800">
                        <div className="bg-violet-600 h-full" style={{ width: `${match.poissonHomeWin}%` }} />
                        <div className="bg-zinc-600 h-full" style={{ width: `${match.poissonDraw}%` }} />
                        <div className="bg-emerald-600 h-full" style={{ width: `${match.poissonAwayWin}%` }} />
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-row lg:flex-col items-center lg:items-end justify-between lg:justify-center border-t lg:border-t-0 lg:border-l border-zinc-800 pt-4 lg:pt-0 lg:pl-6 gap-4 min-w-[200px]">
                    <div className="text-left lg:text-right">
                      <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">Consejo</p>
                      <p className="font-bold text-sm text-violet-400">{match.recommendedBet}</p>
                    </div>
                    <span className="flex items-center gap-1.5 px-3 py-1 bg-violet-600/10 text-violet-400 text-xs font-semibold rounded-lg border border-violet-500/20">
                      <Sliders className="w-3.5 h-3.5" />
                      Cuota: {match.realOdds.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'valuebets' && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg">Oportunidades de Value Betting</h3>
                <p className="text-xs text-zinc-400">Cuotas de mercado con margen esperado positivo (+EV)</p>
              </div>
            </div>

            <div className="glass rounded-2xl overflow-hidden border border-[#27272a]">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[#121214] border-b border-zinc-800 text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                      <th className="py-4 px-6">Encuentro</th>
                      <th className="py-4 px-6">Mercado / Pronóstico</th>
                      <th className="py-4 px-6 text-center">Cuota Justa (Modelo)</th>
                      <th className="py-4 px-6 text-center">Cuota de Mercado</th>
                      <th className="py-4 px-6 text-center">Edge (%)</th>
                      <th className="py-4 px-6 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 text-sm">
                    {filteredMatches.map((match) => (
                      <tr key={match.id} className="hover:bg-[#121214]/60 transition-colors">
                        <td className="py-4 px-6 font-bold">
                          {match.homeTeam} <span className="text-zinc-500 font-normal">vs</span> {match.awayTeam}
                        </td>
                        <td className="py-4 px-6">
                          <span className="bg-zinc-800 text-zinc-300 text-xs font-medium px-2.5 py-1 rounded">
                            {match.recommendedBet}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-center font-mono text-zinc-400">{match.valueOdds.toFixed(2)}</td>
                        <td className="py-4 px-6 text-center font-mono text-zinc-100 font-bold">{match.realOdds.toFixed(2)}</td>
                        <td className="py-4 px-6 text-center">
                          <span className="text-emerald-400 font-bold font-mono">+{match.edge}%</span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <button className="px-3.5 py-1.5 bg-violet-600 hover:bg-violet-700 text-xs font-semibold text-white rounded-lg transition-colors flex items-center gap-1.5 ml-auto">
                            <DollarSign className="w-3.5 h-3.5" />
                            Apostar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
