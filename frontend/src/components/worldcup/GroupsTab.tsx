import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Zap, RefreshCw } from 'lucide-react';

export default function GroupsTab({ state }: { state: any }) {
  const { groups, simulatingGroupsProgress, simulateGroupStage, generateBracketFromGroups } = state;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-900/80 p-4 rounded-xl border border-slate-800">
        <div>
          <h3 className="text-xl font-bold text-[#f3e5ab]">Simulador Fase de Grupos</h3>
          <p className="text-sm text-slate-400">Juega los 72 partidos matemáticamente (Distribución de Poisson)</p>
        </div>
        <Button onClick={simulateGroupStage} disabled={simulatingGroupsProgress !== null} className="bg-[#d4af37] hover:bg-[#c9a520] text-black font-bold">
          {simulatingGroupsProgress ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
          {simulatingGroupsProgress ? 'Simulando...' : 'Simular Todos los Grupos'}
        </Button>
      </div>

      {simulatingGroupsProgress && (
        <Card className="bg-slate-900 border-slate-800 p-6 text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-[#d4af37] mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-200">Simulando el Mundial</h3>
          <p className="text-slate-400">{simulatingGroupsProgress.message}</p>
          <div className="w-full bg-slate-800 h-2 mt-4 rounded-full overflow-hidden">
            <div className="bg-[#d4af37] h-full transition-all" style={{ width: `${(simulatingGroupsProgress.current / simulatingGroupsProgress.total) * 100}%` }} />
          </div>
        </Card>
      )}

      {!simulatingGroupsProgress && groups[0].teams[0].played > 0 && (
        <div className="flex justify-center mb-8">
          <Button onClick={generateBracketFromGroups} className="bg-green-600 hover:bg-green-500 text-white font-bold px-8 py-6 text-lg shadow-[0_0_20px_rgba(22,163,74,0.4)] animate-pulse">
            Continuar a Eliminatorias (Bracket) ➡️
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        {groups.map((group: any) => (
          <Card key={group.name} className="bg-slate-900 border-slate-800 overflow-hidden">
            <div className="bg-slate-950 px-4 py-2 border-b border-slate-800">
              <h3 className="font-bold text-[#f3e5ab] text-center tracking-widest">{group.name}</h3>
            </div>
            <CardContent className="p-0">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900 text-slate-400">
                  <tr>
                    <th className="px-2 py-2 text-center w-8">#</th>
                    <th className="px-2 py-2">País</th>
                    <th className="px-1 py-2 text-center" title="Partidos Jugados">PJ</th>
                    <th className="px-1 py-2 text-center" title="Diferencia de Goles">DG</th>
                    <th className="px-2 py-2 text-center font-bold text-slate-200">PTS</th>
                  </tr>
                </thead>
                <tbody>
                  {group.teams.map((team: any, tIndex: number) => (
                    <tr key={team.name} className={`border-b border-slate-800/30 ${tIndex < 2 ? 'bg-green-900/10' : tIndex === 2 ? 'bg-yellow-900/10' : 'opacity-60'}`}>
                      <td className="px-2 py-2 text-slate-500 font-mono text-center">{tIndex + 1}</td>
                      <td className="px-2 py-2 font-medium break-words whitespace-normal leading-tight min-w-[100px]">
                        <span className="break-words">{team.name}</span>
                      </td>
                      <td className="px-1 py-2 text-center text-slate-400">{team.played}</td>
                      <td className="px-1 py-2 text-center text-slate-400">{team.gd > 0 ? `+${team.gd}` : team.gd}</td>
                      <td className="px-2 py-2 text-center font-bold text-[#f3e5ab]">{team.pts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
