import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { RefreshCw, Zap, ZoomIn, ZoomOut, Trophy } from 'lucide-react';
import { getFlag } from './utils';

export default function BracketTab({ state }: { state: any }) {
  const { 
    bracket, simulatingBracket, simulatingAll, bracketZoom, setBracketZoom,
    generateBracketFromGroups, handleSimulateAll, handleSimulateSingle, openMatchStatsModal
  } = state;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-slate-900/80 p-4 rounded-xl border border-slate-800 mb-2">
        <div>
          <h3 className="text-xl font-bold text-[#f3e5ab]">Árbol de Eliminatorias</h3>
          <p className="text-sm text-slate-400">Simula la fase final usando el motor probabilístico de Poisson</p>
        </div>
        
        <div className="flex items-center gap-6">
          {/* Zoom Controls */}
          <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <Button size={"icon" as any} variant={"ghost" as any} className="h-8 w-8 text-slate-400 hover:text-white" onClick={() => setBracketZoom((z: number) => Math.max(0.3, z - 0.1))}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-xs font-mono w-10 text-center text-slate-300">{Math.round(bracketZoom * 100)}%</span>
            <Button size={"icon" as any} variant={"ghost" as any} className="h-8 w-8 text-slate-400 hover:text-white" onClick={() => setBracketZoom((z: number) => Math.min(1.5, z + 0.1))}>
              <ZoomIn className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex gap-2">
            <Button onClick={generateBracketFromGroups} variant={"outline" as any} className="border-slate-700 hover:bg-slate-800 h-10">
              <RefreshCw className="w-4 h-4 mr-2" /> Reiniciar
            </Button>
            <Button onClick={handleSimulateAll} disabled={simulatingAll} className="bg-[#d4af37] hover:bg-[#c9a520] text-black font-bold h-10 shadow-[0_0_15px_rgba(212,175,55,0.4)]">
              {simulatingAll ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
              Simular Todo
            </Button>
          </div>
        </div>
      </div>

      <div className="overflow-auto bg-slate-950/50 rounded-xl border border-slate-800/50" style={{ height: '70vh' }}>
        <div 
          className="flex gap-12 min-w-max p-8 transition-transform duration-200 origin-top-left"
          style={{ transform: `scale(${bracketZoom})` }}
        >
          {/* Bracket Columns */}
          {['R32', 'R16', 'QF', 'SF', 'F'].map((round, colIndex) => {
            const roundMatches = Object.values(bracket).filter((m: any) => m.round === round) as any[];
            
            // Group matches into pairs for proper tree connection lines
            const pairs = [];
            for (let i = 0; i < roundMatches.length; i += 2) {
              pairs.push([roundMatches[i], roundMatches[i + 1]]);
            }

            return (
              <div key={round} className="flex flex-col justify-around gap-2" style={{ width: '180px' }}>
                <div className="text-center font-bold text-slate-500 mb-2 uppercase tracking-widest text-[10px]">
                  {round === 'R32' ? 'Dieciseisavos' : round === 'R16' ? 'Octavos' : round === 'QF' ? 'Cuartos' : round === 'SF' ? 'Semifinal' : 'Final'}
                </div>
                {pairs.map((pair, pIdx) => (
                  <div key={pIdx} className="relative flex-1 flex flex-col justify-around min-h-[100px]">
                    {pair.map((m) => {
                      if (!m) return null;
                      return (
                        <div key={m.id} className="relative my-2">
                          <Card className={`bg-slate-900 border ${m.winner ? 'border-[#d4af37]/50 shadow-[0_0_10px_rgba(212,175,55,0.1)]' : 'border-slate-800'} overflow-hidden relative z-10 rounded-md`}>
                            <div className="flex flex-col text-[11px]">
                              {/* Home Team */}
                              <div className={`flex items-center justify-between px-2 py-1.5 border-b border-slate-800/50 ${m.winner === 'home' ? 'bg-[#d4af37]/10' : ''}`}>
                                <div className="flex items-center gap-1.5 truncate">
                                  <span className={`truncate ${m.winner === 'away' ? 'text-slate-500 line-through' : 'text-slate-200 font-medium'}`}>{m.home_team ? m.home_team.name : 'TBD'}</span>
                                </div>
                                <span className={`font-mono font-bold ${m.winner === 'home' ? 'text-[#d4af37]' : 'text-slate-400'}`}>{m.home_score !== null ? m.home_score : '-'}</span>
                              </div>
                              {/* Away Team */}
                              <div className={`flex items-center justify-between px-2 py-1.5 ${m.winner === 'away' ? 'bg-[#d4af37]/10' : ''}`}>
                                <div className="flex items-center gap-1.5 truncate">
                                  <span className={`truncate ${m.winner === 'home' ? 'text-slate-500 line-through' : 'text-slate-200 font-medium'}`}>{m.away_team ? m.away_team.name : 'TBD'}</span>
                                </div>
                                <span className={`font-mono font-bold ${m.winner === 'away' ? 'text-[#d4af37]' : 'text-slate-400'}`}>{m.away_score !== null ? m.away_score : '-'}</span>
                              </div>
                            </div>
                            
                            {/* Simulate Overlay Button */}
                            {!m.winner && m.home_team && m.away_team && (
                              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-[1px] flex flex-col items-center justify-center gap-1 opacity-0 hover:opacity-100 transition-opacity">
                                <Button size={"sm" as any} onClick={() => handleSimulateSingle(m.id)} disabled={simulatingBracket === m.id} className="bg-[#d4af37]/20 hover:bg-[#d4af37]/40 text-[#d4af37] border border-[#d4af37]/50 h-6 text-[10px] px-2 py-0 w-[80%]">
                                  {simulatingBracket === m.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : '⚡ Simular'}
                                </Button>
                                <Button size={"sm" as any} onClick={() => openMatchStatsModal(m.id, m.home_team.apiId, m.away_team.apiId, m.home_team.name, m.away_team.name)} className="bg-blue-500/20 hover:bg-blue-500/40 text-blue-400 border border-blue-500/50 h-6 text-[10px] px-2 py-0 w-[80%]">
                                  📊 Cuotas
                                </Button>
                              </div>
                            )}
                          </Card>
                          
                          {/* Horizontal Stub Out to the Right */}
                          {colIndex < 4 && (
                            <div className="absolute top-1/2 -right-6 w-6 border-t-2 border-slate-700/60 z-0" />
                          )}
                        </div>
                      );
                    })}

                    {/* Vertical line connecting the pair */}
                    {colIndex < 4 && pair[1] && (
                      <div className="absolute -right-6 border-r-2 border-slate-700/60 z-0" style={{ top: '25%', bottom: '25%' }} />
                    )}
                    
                    {/* Horizontal stub connecting to next round card */}
                    {colIndex < 4 && pair[1] && (
                      <div className="absolute top-1/2 -right-12 w-6 border-t-2 border-slate-700/60 z-0" />
                    )}
                  </div>
                ))}
              </div>
            );
          })}
          
          {/* Champion Box */}
          <div className="flex flex-col justify-center" style={{ width: '220px' }}>
            <div className="text-center font-bold text-[#d4af37] mb-4 uppercase tracking-widest text-xs">Campeón</div>
            <Card className="bg-gradient-to-b from-[#d4af37]/20 to-slate-900 border-[#d4af37] border-2 shadow-[0_0_30px_rgba(212,175,55,0.3)] overflow-hidden">
              <CardContent className="p-6 text-center">
                <Trophy className="w-16 h-16 text-[#d4af37] mx-auto mb-4" />
                {bracket['F-1'].winner ? (
                  <div>
                    <div className="text-4xl mb-2">{getFlag((bracket['F-1'] as any)[`${bracket['F-1'].winner}_team`].name)}</div>
                    <h2 className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-[#d4af37] to-[#f3e5ab] uppercase">
                      {(bracket['F-1'] as any)[`${bracket['F-1'].winner}_team`].name}
                    </h2>
                  </div>
                ) : (
                  <span className="text-slate-500 font-bold uppercase tracking-widest">TBD</span>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
