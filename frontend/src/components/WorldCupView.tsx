import { useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Download, RefreshCw } from 'lucide-react';

import { useWorldCup } from '../hooks/useWorldCup';

import GroupsTab from './worldcup/GroupsTab';
import FixturesTab from './worldcup/FixturesTab';
import PredictionsTab from './worldcup/PredictionsTab';
import BracketTab from './worldcup/BracketTab';
import MatchStatsModal from './worldcup/MatchStatsModal';

export default function WorldCupView() {
  const state = useWorldCup();

  // Load initial data
  useEffect(() => {
    state.loadFixtures();
    state.fetchPredictions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      {/* Header & Sync Status */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#d4af37]/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        
        <div className="relative z-10">
          <h2 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-[#d4af37] to-[#f3e5ab] uppercase tracking-tighter">
            Mundial 2026
          </h2>
          <p className="text-slate-400 mt-1">Simulador Matemático & Polla (Distribución de Poisson)</p>
        </div>

        <div className="flex flex-col items-end gap-2 relative z-10">
          {state.syncStatus?.running ? (
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 animate-spin text-[#d4af37]" />
              <div className="text-right">
                <div className="text-sm font-bold text-[#f3e5ab]">Sincronizando {state.syncStatus.processed}/{state.syncStatus.total}</div>
                <div className="text-xs text-slate-400">{state.syncStatus.current_team}</div>
              </div>
            </div>
          ) : (
            <div className="flex gap-2">
              <Button onClick={state.startDataSync} className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-bold text-xs">
                Actualizar Elos y Plantillas
              </Button>
              <Button onClick={state.startSync} disabled={state.syncing} className="bg-[#d4af37]/20 hover:bg-[#d4af37]/30 text-[#d4af37] border border-[#d4af37]/30 font-bold shadow-[0_0_15px_rgba(212,175,55,0.15)]">
                {state.syncing ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                {state.syncing ? 'Sincronizando...' : 'Descargar Data del Mundial'}
              </Button>
            </div>
          )}
          {state.syncStatus?.errors && state.syncStatus.errors.length > 0 && (
            <Badge variant={"destructive" as any} className="text-[10px]">
              {state.syncStatus.errors.length} errores
            </Badge>
          )}
        </div>
      </div>

      {/* Main Navigation */}
      <Card className="bg-slate-900 border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="flex overflow-x-auto">
          {[
            { id: 'groups', label: 'Fase de Grupos' },
            { id: 'bracket', label: 'Eliminatorias (Árbol)' },
            { id: 'fixtures', label: 'Partidos & Pronósticos' },
            { id: 'predictions', label: 'Mis Puntos' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => state.setActiveTab(tab.id as any)}
              className={`flex-1 min-w-[150px] py-4 px-4 text-sm font-bold tracking-wide transition-all ${
                state.activeTab === tab.id 
                  ? 'bg-slate-950 text-[#f3e5ab] border-b-2 border-[#d4af37]' 
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </Card>

      {/* TABS CONTENT */}
      {state.activeTab === 'groups' && <GroupsTab state={state} />}
      {state.activeTab === 'fixtures' && <FixturesTab state={state} />}
      {state.activeTab === 'predictions' && <PredictionsTab state={state} />}
      {state.activeTab === 'bracket' && <BracketTab state={state} />}

      {/* MODAL */}
      <MatchStatsModal state={state} />

    </div>
  );
}
