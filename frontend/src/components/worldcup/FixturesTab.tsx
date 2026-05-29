import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Swords, RefreshCw, Zap, BarChart3 } from 'lucide-react';
import { getFlag } from './utils';

export default function FixturesTab({ state }: { state: any }) {
  const { 
    fixtures, loadingFixtures, 
    predictions, scoreInputs, setScoreInputs,
    loadingStats, openMatchStatsModal,
    savingId, savePrediction
  } = state;

  const existingPredictionMap: Record<number, any> = {};
  for (const p of predictions) {
    existingPredictionMap[p.fixture_id] = p;
  }

  return (
    <div className="space-y-4">
      {loadingFixtures ? (
        <div className="flex justify-center py-12"><RefreshCw className="w-8 h-8 animate-spin text-[#d4af37]" /></div>
      ) : fixtures.length === 0 ? (
        <Card className="bg-slate-900 border-slate-800 border-dashed p-12 text-center">
          <Swords className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-300">No hay partidos del Mundial en la base de datos</h3>
          <p className="text-slate-500 mt-2">Presiona "⚡ Descargar Data del Mundial" para sincronizar los fixtures oficiales.</p>
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-end mb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-200">Partidos Oficiales</h3>
              <p className="text-sm text-slate-400">Ingresa tus pronósticos para sumar puntos en la Polla</p>
            </div>
            <Badge className="bg-slate-800 text-slate-300">
              {fixtures.length} partidos cargados
            </Badge>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {fixtures.map((f: any) => {
              const existing = existingPredictionMap[f.id];
              const input = scoreInputs[f.id] || { home: '', away: '' };
              const hasResult = f.home_score !== null;
              
              return (
                <Card key={f.id} className={`bg-slate-900 border-slate-800 overflow-hidden ${existing ? 'border-l-2 border-l-[#d4af37]' : ''}`}>
                  <CardContent className="py-3 px-4">
                    <div className="flex flex-col md:flex-row items-center gap-4">
                      {/* Date */}
                      <div className="text-xs text-slate-500 w-24 text-center shrink-0">
                        {f.date ? new Date(f.date).toLocaleDateString('es', { day: '2-digit', month: 'short' }) : '-'}
                        <br />
                        {f.date ? new Date(f.date).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }) : ''}
                      </div>
                      
                      {/* Match */}
                      <div className="flex-grow flex items-center justify-center gap-3 text-center min-w-0">
                        <span className="text-sm font-semibold text-slate-200 text-right flex-1 truncate">
                          {getFlag(f.home_team_name)} {f.home_team_name}
                        </span>
                        
                        {/* Score inputs */}
                        <div className="flex items-center gap-1 shrink-0">
                          <input
                            type="number" min="0" max="20"
                            value={input.home}
                            onChange={e => setScoreInputs((prev: any) => ({ ...prev, [f.id]: { ...prev[f.id], home: e.target.value, away: prev[f.id]?.away || '' } }))}
                            className="w-10 h-8 text-center rounded-md bg-slate-800 border border-slate-700 text-white text-sm font-mono focus:border-[#d4af37] focus:outline-none"
                            placeholder="-"
                          />
                          <span className="text-slate-500 font-bold">-</span>
                          <input
                            type="number" min="0" max="20"
                            value={input.away}
                            onChange={e => setScoreInputs((prev: any) => ({ ...prev, [f.id]: { home: prev[f.id]?.home || '', away: e.target.value } }))}
                            className="w-10 h-8 text-center rounded-md bg-slate-800 border border-slate-700 text-white text-sm font-mono focus:border-[#d4af37] focus:outline-none"
                            placeholder="-"
                          />
                        </div>
                        
                        <span className="text-sm font-semibold text-slate-200 text-left flex-1 truncate">
                          {f.away_team_name} {getFlag(f.away_team_name)}
                        </span>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          size="sm"
                          onClick={() => openMatchStatsModal(f.id, f.home_team_id, f.away_team_id, f.home_team_name, f.away_team_name)}
                          disabled={loadingStats[f.id]}
                          variant="outline"
                          className="text-xs px-2 h-8 bg-slate-800 border-slate-700 hover:bg-slate-700"
                          title="Ver Cuotas (Odds)"
                        >
                          {loadingStats[f.id] ? <RefreshCw className="w-3 h-3 animate-spin" /> : <BarChart3 className="w-3 h-3 text-blue-400" />}
                        </Button>
                        
                        <Button
                          size="sm"
                          onClick={() => savePrediction(f.id)}
                          disabled={savingId === f.id || !input.home || !input.away}
                          className="bg-[#d4af37]/20 hover:bg-[#d4af37]/30 text-[#d4af37] border border-[#d4af37]/30 text-xs px-3 h-8"
                        >
                          {savingId === f.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                          <span className="ml-1 hidden md:inline">{existing ? 'Actualizar' : 'Guardar'}</span>
                        </Button>
                        
                        {hasResult && (
                          <Badge className="text-xs bg-slate-800">
                            Real: {f.home_score}-{f.away_score}
                          </Badge>
                        )}
                        
                        {existing && existing.points > 0 && (
                          <Badge className="text-xs bg-green-900/50 text-green-400 border-green-700">
                            +{existing.points}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
