import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { RefreshCw, X } from 'lucide-react';
import { getFlag, getOdds } from './utils';

export default function MatchStatsModal({ state }: { state: any }) {
  const { selectedMatchModal, setSelectedMatchModal, loadingStats, matchStats } = state;

  if (!selectedMatchModal) return null;

  const id = selectedMatchModal.id;
  const loading = loadingStats[id];
  const stats = matchStats[id];

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <Card className="bg-slate-950 border-slate-800 w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl relative">
        
        {/* Modal Header */}
        <div className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur-md border-b border-slate-800 p-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="text-xl font-bold flex items-center gap-3">
              <span>{getFlag(selectedMatchModal.homeName)}</span>
              <span className="text-slate-200">{selectedMatchModal.homeName}</span>
            </div>
            <span className="text-slate-500 font-bold italic">VS</span>
            <div className="text-xl font-bold flex items-center gap-3">
              <span className="text-slate-200">{selectedMatchModal.awayName}</span>
              <span>{getFlag(selectedMatchModal.awayName)}</span>
            </div>
          </div>
          <Button size="icon" variant="ghost" onClick={() => setSelectedMatchModal(null)} className="text-slate-400 hover:text-white rounded-full">
            <X className="w-6 h-6" />
          </Button>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-[#d4af37] mb-4" />
              <p>Calculando cuotas y probabilidades con el motor de Poisson...</p>
            </div>
          ) : stats ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Left Column: Main Markets */}
              <div className="lg:col-span-2 space-y-6">
                
                {/* Market: 1X2 Match Winner */}
                <Card className="bg-slate-900 border-slate-800 p-0 overflow-hidden">
                  <div className="bg-slate-800/50 p-3 border-b border-slate-800">
                    <h3 className="font-bold text-slate-300 flex justify-between items-center text-sm">
                      <span>Ganador del Partido (1X2)</span>
                      <Badge variant="outline" className="text-[#d4af37] border-[#d4af37]/30 bg-[#d4af37]/10">Mercado Principal</Badge>
                    </h3>
                  </div>
                  <div className="p-4 grid grid-cols-3 gap-3">
                    <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 hover:border-[#d4af37]/50 cursor-pointer transition-colors group">
                      <div className="text-xs text-slate-400 mb-1 font-semibold">{selectedMatchModal.homeName} (1)</div>
                      <div className="flex justify-between items-end">
                        <span className="text-2xl font-black text-[#f3e5ab]">{getOdds(stats['1x2']?.home_win)}</span>
                        <span className="text-xs text-green-400">{(stats['1x2']?.home_win * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 hover:border-slate-600 cursor-pointer transition-colors group">
                      <div className="text-xs text-slate-400 mb-1 font-semibold">Empate (X)</div>
                      <div className="flex justify-between items-end">
                        <span className="text-2xl font-black text-slate-300">{getOdds(stats['1x2']?.draw)}</span>
                        <span className="text-xs text-yellow-400">{(stats['1x2']?.draw * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 hover:border-blue-500/50 cursor-pointer transition-colors group">
                      <div className="text-xs text-slate-400 mb-1 font-semibold">{selectedMatchModal.awayName} (2)</div>
                      <div className="flex justify-between items-end">
                        <span className="text-2xl font-black text-blue-400">{getOdds(stats['1x2']?.away_win)}</span>
                        <span className="text-xs text-blue-400">{(stats['1x2']?.away_win * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Goals Markets (BTTS & Over/Under) */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Both Teams To Score */}
                  <Card className="bg-slate-900 border-slate-800 p-0 overflow-hidden">
                    <div className="bg-slate-800/50 p-2.5 border-b border-slate-800">
                      <h3 className="font-bold text-slate-300 text-xs">Ambos Equipos Marcan</h3>
                    </div>
                    <div className="p-3 grid grid-cols-2 gap-2">
                      <div className="bg-slate-950 border border-slate-800 rounded p-2 text-center">
                        <div className="text-[10px] text-slate-400 uppercase">Sí</div>
                        <div className="font-bold text-[#f3e5ab]">{getOdds(stats.btts?.yes)}</div>
                        <div className="text-[10px] text-slate-500">{(stats.btts?.yes * 100).toFixed(0)}%</div>
                      </div>
                      <div className="bg-slate-950 border border-slate-800 rounded p-2 text-center">
                        <div className="text-[10px] text-slate-400 uppercase">No</div>
                        <div className="font-bold text-slate-300">{getOdds(stats.btts?.no)}</div>
                        <div className="text-[10px] text-slate-500">{(stats.btts?.no * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </Card>

                  {/* Over / Under 2.5 */}
                  <Card className="bg-slate-900 border-slate-800 p-0 overflow-hidden">
                    <div className="bg-slate-800/50 p-2.5 border-b border-slate-800">
                      <h3 className="font-bold text-slate-300 text-xs">Total de Goles (2.5)</h3>
                    </div>
                    <div className="p-3 grid grid-cols-2 gap-2">
                      <div className="bg-slate-950 border border-slate-800 rounded p-2 text-center">
                        <div className="text-[10px] text-slate-400 uppercase">Más de 2.5</div>
                        <div className="font-bold text-[#f3e5ab]">{getOdds(stats.over_under?.['2.5']?.over)}</div>
                        <div className="text-[10px] text-slate-500">{(stats.over_under?.['2.5']?.over * 100).toFixed(0)}%</div>
                      </div>
                      <div className="bg-slate-950 border border-slate-800 rounded p-2 text-center">
                        <div className="text-[10px] text-slate-400 uppercase">Menos de 2.5</div>
                        <div className="font-bold text-slate-300">{getOdds(stats.over_under?.['2.5']?.under)}</div>
                        <div className="text-[10px] text-slate-500">{(stats.over_under?.['2.5']?.under * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </Card>
                </div>

                {/* Exact Scores (Top 5) */}
                <Card className="bg-slate-900 border-slate-800 p-0 overflow-hidden">
                  <div className="bg-slate-800/50 p-3 border-b border-slate-800 flex justify-between items-center">
                    <h3 className="font-bold text-slate-300 text-sm">Marcadores Exactos (Top 5 Probables)</h3>
                  </div>
                  <div className="p-4 flex gap-3 overflow-x-auto">
                    {Object.entries(stats.correct_score_top5 || {}).map(([score, prob]: [string, any]) => (
                      <div key={score} className="bg-slate-950 border border-slate-800 rounded-lg p-3 min-w-[100px] flex-shrink-0 text-center">
                        <div className="text-xl font-bold font-mono text-[#f3e5ab] tracking-widest">{score}</div>
                        <div className="text-sm font-semibold text-white mt-1">{getOdds(prob)}</div>
                        <div className="text-[10px] text-slate-500 mt-1">{(prob * 100).toFixed(1)}% prob.</div>
                      </div>
                    ))}
                  </div>
                </Card>

              </div>

              {/* Right Column: Deep Stats (xG, Ratings, Props) */}
              <div className="space-y-4">
                
                {/* Power Ratings */}
                <Card className="bg-slate-900 border-slate-800 p-4">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Métricas del Simulador</h4>
                  
                  <div className="mb-4">
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Squad Rating</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-[#d4af37] w-8">{stats.squad_rating?.home || "6.5"}</span>
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full flex">
                         <div className="bg-[#d4af37] h-full" style={{ width: `${(stats.squad_rating?.home / 10) * 100}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="font-mono text-sm text-blue-400 w-8">{stats.squad_rating?.away || "6.5"}</span>
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full flex">
                         <div className="bg-blue-400 h-full" style={{ width: `${(stats.squad_rating?.away / 10) * 100}%` }} />
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Expected Goals (xG)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-[#d4af37] w-8">{stats.expected_goals?.home || "1.2"}</span>
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full flex">
                         <div className="bg-[#d4af37] h-full" style={{ width: `${Math.min((stats.expected_goals?.home / 3) * 100, 100)}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="font-mono text-sm text-blue-400 w-8">{stats.expected_goals?.away || "1.0"}</span>
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full flex">
                         <div className="bg-blue-400 h-full" style={{ width: `${Math.min((stats.expected_goals?.away / 3) * 100, 100)}%` }} />
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Propositional Stats (Corners/Cards) */}
                <Card className="bg-slate-900 border-slate-800 p-4">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Props Especiales</h4>
                  
                  <div className="flex items-center justify-between py-2 border-b border-slate-800">
                    <span className="text-sm text-slate-300">Total Córners (Línea 9.5)</span>
                    <div className="text-right">
                      <div className="font-bold text-[#f3e5ab]">{stats.corners?.total ? stats.corners.total.toFixed(1) : '9.2'}</div>
                      <div className="text-[10px] text-slate-500">Estimados</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between py-2 border-b border-slate-800">
                    <span className="text-sm text-slate-300">Total Tarjetas (Línea 3.5)</span>
                    <div className="text-right">
                      <div className="font-bold text-[#f3e5ab]">{stats.cards?.total ? stats.cards.total.toFixed(1) : '3.8'}</div>
                      <div className="text-[10px] text-slate-500">Estimadas</div>
                    </div>
                  </div>

                </Card>
                
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-slate-500">Error al cargar datos.</div>
          )}
        </div>
      </Card>
    </div>
  );
}
