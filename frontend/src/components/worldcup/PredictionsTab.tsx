import { Card, CardContent } from '../ui/card';
import { Trophy } from 'lucide-react';
import { getFlag } from './utils';

export default function PredictionsTab({ state }: { state: any }) {
  const { predictions, totalPoints } = state;

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-r from-slate-900 to-[#d4af37]/10 border-slate-800">
        <CardContent className="p-6 flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-slate-200">Mis Puntos Acumulados</h3>
            <p className="text-sm text-slate-400">Total de puntos obtenidos en la Polla Mundialista</p>
          </div>
          <div className="flex items-center gap-3">
            <Trophy className="w-10 h-10 text-[#d4af37]" />
            <span className="text-5xl font-black text-[#f3e5ab]">{totalPoints}</span>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900 border-slate-800 overflow-hidden">
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs pt-6">
            {[
              { label: '🎯 Marcador exacto', pts: 12, color: 'text-green-400' },
              { label: '✅ Ganador + Dif. goles', pts: 8, color: 'text-blue-400' },
              { label: '🤝 Empate correcto', pts: 8, color: 'text-blue-400' },
              { label: '👍 Ganador correcto', pts: 5, color: 'text-yellow-400' },
              { label: '🔢 Goles parciales', pts: 2, color: 'text-orange-400' },
              { label: '❌ Incorrecto', pts: 0, color: 'text-slate-500' },
            ].map(r => (
              <div key={r.label} className="flex justify-between items-center px-3 py-2 rounded-lg bg-slate-800/50">
                <span className="text-slate-300">{r.label}</span>
                <span className={`font-bold font-mono ${r.color}`}>{r.pts}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {predictions.length === 0 ? (
        <Card className="bg-slate-900 border-slate-800 border-dashed p-8 text-center">
          <p className="text-slate-500">Aún no has realizado predicciones. Ve a la pestaña "Partidos & Pronósticos" para empezar.</p>
        </Card>
      ) : (
        <Card className="bg-slate-900 border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-slate-400 uppercase bg-slate-950 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left">Partido</th>
                  <th className="px-4 py-3 text-center">Tu Predicción</th>
                  <th className="px-4 py-3 text-center">Resultado Real</th>
                  <th className="px-4 py-3 text-center">Puntos</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((p: any) => (
                  <tr key={p.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-slate-200">
                      {getFlag(p.home_team)} {p.home_team} vs {p.away_team} {getFlag(p.away_team)}
                    </td>
                    <td className="px-4 py-3 text-center font-mono font-bold text-[#f3e5ab]">
                      {p.predicted_home} - {p.predicted_away}
                    </td>
                    <td className="px-4 py-3 text-center font-mono">
                      {p.actual_home !== null ? (
                        <span className="text-slate-300">{p.actual_home} - {p.actual_away}</span>
                      ) : (
                        <span className="text-slate-600">Pendiente</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {p.actual_home !== null ? (
                        <span className={`font-bold ${p.points >= 8 ? 'text-green-400' : p.points >= 5 ? 'text-yellow-400' : p.points > 0 ? 'text-orange-400' : 'text-slate-500'}`}>
                          {p.label || `${p.points} pts`}
                        </span>
                      ) : (
                        <span className="text-slate-600">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
