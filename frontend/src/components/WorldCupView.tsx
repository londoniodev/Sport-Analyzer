import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Trophy, ChevronUp, ChevronDown, Swords, Globe2 } from 'lucide-react';
import { worldCupGroups, Team } from '../lib/worldCupData';

export default function WorldCupView() {
  const [activeTab, setActiveTab] = useState<'groups' | 'knockout'>('groups');
  
  // Initialize state with default order
  const [groups, setGroups] = useState(
    worldCupGroups.map(g => ({ ...g, teams: [...g.teams] }))
  );

  const moveTeam = (groupIndex: number, teamIndex: number, direction: 'up' | 'down') => {
    setGroups(prev => {
      const newGroups = [...prev];
      const group = { ...newGroups[groupIndex] };
      const teams = [...group.teams];
      
      if (direction === 'up' && teamIndex > 0) {
        [teams[teamIndex], teams[teamIndex - 1]] = [teams[teamIndex - 1], teams[teamIndex]];
      } else if (direction === 'down' && teamIndex < teams.length - 1) {
        [teams[teamIndex], teams[teamIndex + 1]] = [teams[teamIndex + 1], teams[teamIndex]];
      }
      
      group.teams = teams;
      newGroups[groupIndex] = group;
      return newGroups;
    });
  };

  // Compute qualified teams: Top 2 of each (24) + 8 best thirds
  const qualifiedTeams = useMemo(() => {
    const top2: Team[] = [];
    const thirds: Team[] = [];
    
    groups.forEach(g => {
      top2.push(g.teams[0], g.teams[1]);
      thirds.push(g.teams[2]);
    });
    
    // Auto-select the first 8 thirds just to fill the bracket for the simulation
    const bestThirds = thirds.slice(0, 8);
    return [...top2, ...bestThirds];
  }, [groups]);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-[#d4af37] to-[#f3e5ab] flex items-center gap-3">
            <Trophy className="w-8 h-8 text-[#d4af37]" /> Copa Mundial 2026
          </h2>
          <p className="text-slate-400 mt-2">Simulador interactivo y predicciones de la Fase de Grupos</p>
        </div>
        
        <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('groups')}
            className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'groups' 
              ? 'bg-[#d4af37]/20 text-[#f3e5ab] shadow-[inset_0_0_10px_rgba(212,175,55,0.2)]' 
              : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Fase de Grupos
          </button>
          <button
            onClick={() => setActiveTab('knockout')}
            className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'knockout' 
              ? 'bg-[#d4af37]/20 text-[#f3e5ab] shadow-[inset_0_0_10px_rgba(212,175,55,0.2)]' 
              : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Fase Final
          </button>
        </div>
      </div>

      {activeTab === 'groups' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {groups.map((group, gIndex) => (
            <Card key={group.name} className="bg-gradient-to-b from-slate-900 to-slate-950 border-slate-800 shadow-xl overflow-hidden hover:border-[#d4af37]/30 transition-colors">
              <CardHeader className="bg-slate-950/50 border-b border-slate-800/50 py-3">
                <CardTitle className="text-lg text-center text-[#d4af37] font-bold tracking-widest uppercase">
                  {group.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {group.teams.map((team, tIndex) => (
                  <div 
                    key={team.name} 
                    className={`flex items-center justify-between p-3 border-b border-slate-800/30 last:border-0 transition-colors
                      ${tIndex < 2 ? 'bg-green-900/10' : tIndex === 2 ? 'bg-yellow-900/10' : 'bg-red-900/10 opacity-70'}
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`font-mono font-bold w-4 text-center ${
                        tIndex < 2 ? 'text-green-500' : tIndex === 2 ? 'text-yellow-500' : 'text-slate-600'
                      }`}>
                        {tIndex + 1}
                      </span>
                      <span className="text-2xl" title={team.name}>{team.flag}</span>
                      <span className="font-medium text-slate-200 text-sm">{team.name}</span>
                    </div>
                    
                    <div className="flex flex-col gap-1">
                      <button 
                        onClick={() => moveTeam(gIndex, tIndex, 'up')}
                        disabled={tIndex === 0}
                        className="text-slate-500 hover:text-white disabled:opacity-30 disabled:hover:text-slate-500"
                      >
                        <ChevronUp className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => moveTeam(gIndex, tIndex, 'down')}
                        disabled={tIndex === 3}
                        className="text-slate-500 hover:text-white disabled:opacity-30 disabled:hover:text-slate-500"
                      >
                        <ChevronDown className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'knockout' && (
        <Card className="bg-slate-900 border-slate-800 p-8 min-h-[600px] flex items-center justify-center border-dashed">
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#d4af37]/20 text-[#d4af37] mb-4">
              <Swords className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-bold text-slate-200">Fase Eliminatoria (32 Equipos)</h3>
            <p className="text-slate-400 max-w-md mx-auto">
              Se han clasificado {qualifiedTeams.length} equipos basados en tu predicción.
              El Bracket interactivo estará disponible en la próxima actualización.
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-6">
              {qualifiedTeams.map(t => (
                <span key={t.name} className="px-3 py-1 bg-slate-800 rounded-full text-sm border border-slate-700">
                  {t.flag} {t.name}
                </span>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
