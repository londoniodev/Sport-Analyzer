import { useState, useEffect, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Trophy, Swords, Download, RefreshCw, Zap, BarChart3 } from 'lucide-react';
import { worldCupGroups } from '../lib/worldCupData';

interface SyncStatus {
  running: boolean;
  total: number;
  processed: number;
  current_team: string;
  errors: string[];
}

interface WCFixture {
  id: number;
  date: string;
  home_team_id: number;
  away_team_id: number;
  home_team_name: string;
  away_team_name: string;
  home_score: number | null;
  away_score: number | null;
}

interface Prediction {
  id: number;
  fixture_id: number;
  home_team: string;
  away_team: string;
  predicted_home: number;
  predicted_away: number;
  actual_home: number | null;
  actual_away: number | null;
  points: number;
  label: string;
}

interface BracketMatch {
  id: string;
  round: 'R32' | 'R16' | 'QF' | 'SF' | 'F';
  home_team: any | null;
  away_team: any | null;
  home_score: number | null;
  away_score: number | null;
  winner: 'home' | 'away' | null;
  nextMatchId: string | null;
  isHomeNext: boolean;
}

const generateInitialBracket = () => {
  const b: Record<string, BracketMatch> = {};
  for (let i = 1; i <= 16; i++) b[`R32-${i}`] = { id: `R32-${i}`, round: 'R32', home_team: null, away_team: null, home_score: null, away_score: null, winner: null, nextMatchId: `R16-${Math.ceil(i/2)}`, isHomeNext: i % 2 !== 0 };
  for (let i = 1; i <= 8; i++) b[`R16-${i}`] = { id: `R16-${i}`, round: 'R16', home_team: null, away_team: null, home_score: null, away_score: null, winner: null, nextMatchId: `QF-${Math.ceil(i/2)}`, isHomeNext: i % 2 !== 0 };
  for (let i = 1; i <= 4; i++) b[`QF-${i}`] = { id: `QF-${i}`, round: 'QF', home_team: null, away_team: null, home_score: null, away_score: null, winner: null, nextMatchId: `SF-${Math.ceil(i/2)}`, isHomeNext: i % 2 !== 0 };
  for (let i = 1; i <= 2; i++) b[`SF-${i}`] = { id: `SF-${i}`, round: 'SF', home_team: null, away_team: null, home_score: null, away_score: null, winner: null, nextMatchId: `F-1`, isHomeNext: i % 2 !== 0 };
  b[`F-1`] = { id: `F-1`, round: 'F', home_team: null, away_team: null, home_score: null, away_score: null, winner: null, nextMatchId: null, isHomeNext: true };
  return b;
};

export default function WorldCupView() {
  const [activeTab, setActiveTab] = useState<'groups' | 'fixtures' | 'predictions' | 'bracket'>('groups');
  const [groups, setGroups] = useState(() => 
    worldCupGroups.map(g => ({
      ...g,
      teams: g.teams.map(t => ({ ...t, played: 0, pts: 0, gf: 0, ga: 0, gd: 0 }))
    }))
  );
  
  // Sync state
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  
  // Fixtures & Predictions
  const [fixtures, setFixtures] = useState<WCFixture[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [totalPoints, setTotalPoints] = useState(0);
  const [loadingFixtures, setLoadingFixtures] = useState(false);
  
  // Score inputs: {fixture_id: {home: number, away: number}}
  const [scoreInputs, setScoreInputs] = useState<Record<number, {home: string, away: string}>>({});
  const [savingId, setSavingId] = useState<number | null>(null);

  // Stats / Probabilities
  const [matchStats, setMatchStats] = useState<Record<number, any>>({});
  const [loadingStats, setLoadingStats] = useState<Record<number, boolean>>({});
  const [expandedStatsId, setExpandedStatsId] = useState<number | null>(null);

  // Bracket State
  const [bracket, setBracket] = useState<Record<string, BracketMatch>>(generateInitialBracket());
  const [simulatingBracket, setSimulatingBracket] = useState<string | null>(null);
  const [simulatingAll, setSimulatingAll] = useState(false);
  
  // Group Simulation State
  const [simulatingGroupsProgress, setSimulatingGroupsProgress] = useState<{current: number, total: number, message: string} | null>(null);
  const simulateGroupStage = async () => {
    setSimulatingGroupsProgress({ current: 0, total: 72, message: 'Preparando calendarios...' });
    
    const updatedGroups = JSON.parse(JSON.stringify(groups));
    let matchesSimulated = 0;
    const matchPairs = [[0,1], [2,3], [0,2], [1,3], [0,3], [1,2]];
    
    for (let gIndex = 0; gIndex < 12; gIndex++) {
       const group = updatedGroups[gIndex];
       
       for (const pair of matchPairs) {
           const teamHome = group.teams[pair[0]];
           const teamAway = group.teams[pair[1]];
           
           if (!teamHome || !teamAway) continue;
           
           setSimulatingGroupsProgress({ current: matchesSimulated, total: 72, message: `Simulando: ${teamHome.name} vs ${teamAway.name}` });
           
           try {
               const res = await fetch(`/api/worldcup/predict/${teamHome.apiId}/${teamAway.apiId}`);
               const data = await res.json();
               
               const topScores = Object.entries(data.correct_score_top5);
               if (topScores && topScores.length > 0) {
                   const mostLikelyScoreStr = topScores[0][0] as string;
                   const [homeScore, awayScore] = mostLikelyScoreStr.split('-').map(Number);
                   
                   teamHome.played += 1;
                   teamAway.played += 1;
                   teamHome.gf += homeScore;
                   teamHome.ga += awayScore;
                   teamHome.gd = teamHome.gf - teamHome.ga;
                   
                   teamAway.gf += awayScore;
                   teamAway.ga += homeScore;
                   teamAway.gd = teamAway.gf - teamAway.ga;
                   
                   if (homeScore > awayScore) {
                       teamHome.pts += 3;
                   } else if (awayScore > homeScore) {
                       teamAway.pts += 3;
                   } else {
                       teamHome.pts += 1;
                       teamAway.pts += 1;
                   }
               }
           } catch (e) { console.error("Sim fail", e); }
           matchesSimulated++;
       }
       
       // Sort the group by FIFA rules (Pts > GD > GF)
       group.teams.sort((a: any, b: any) => {
           if (b.pts !== a.pts) return b.pts - a.pts;
           if (b.gd !== a.gd) return b.gd - a.gd;
           return b.gf - a.gf;
       });
       
       setGroups([...updatedGroups]); // Progressive UI update
    }
    setSimulatingGroupsProgress(null);
  };

  // Start World Cup data sync
  const startSync = async () => {
    setSyncing(true);
    try {
      await fetch('/api/worldcup/sync', { method: 'POST' });
      pollSyncStatus();
    } catch (e) {
      console.error(e);
      setSyncing(false);
    }
  };

  const pollSyncStatus = useCallback(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/worldcup/sync-status');
        const data: SyncStatus = await res.json();
        setSyncStatus(data);
        if (!data.running) {
          clearInterval(interval);
          setSyncing(false);
        }
      } catch {
        clearInterval(interval);
        setSyncing(false);
      }
    }, 3000);
  }, []);

  // Fetch fixtures
  const fetchFixtures = async () => {
    setLoadingFixtures(true);
    try {
      const res = await fetch('/api/worldcup/fixtures');
      const data = await res.json();
      setFixtures(data);
    } catch (e) { console.error(e); }
    finally { setLoadingFixtures(false); }
  };

  // Fetch predictions
  const fetchPredictions = async () => {
    try {
      const res = await fetch('/api/worldcup/predictions');
      const data = await res.json();
      setPredictions(data.predictions || []);
      setTotalPoints(data.total_points || 0);
      
      // Pre-fill score inputs from existing predictions
      const inputs: Record<number, {home: string, away: string}> = {};
      for (const p of data.predictions || []) {
        inputs[p.fixture_id] = { home: String(p.predicted_home), away: String(p.predicted_away) };
      }
      setScoreInputs(prev => ({ ...inputs, ...prev }));
    } catch (e) { console.error(e); }
  };

  // Save a prediction
  const savePrediction = async (fixtureId: number) => {
    const input = scoreInputs[fixtureId];
    if (!input || input.home === '' || input.away === '') return;
    
    setSavingId(fixtureId);
    try {
      await fetch('/api/worldcup/predict-score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fixture_id: fixtureId,
          predicted_home_score: parseInt(input.home),
          predicted_away_score: parseInt(input.away)
        })
      });
      fetchPredictions();
    } catch (e) { console.error(e); }
    finally { setSavingId(null); }
  };

  // Load statistical probabilities for a match
  const loadMatchStats = async (fixture: WCFixture) => {
    if (expandedStatsId === fixture.id) {
      setExpandedStatsId(null);
      return;
    }
    
    if (matchStats[fixture.id]) {
      setExpandedStatsId(fixture.id);
      return;
    }

    setLoadingStats(prev => ({ ...prev, [fixture.id]: true }));
    try {
      const res = await fetch(`/api/worldcup/predict/${fixture.home_team_id}/${fixture.away_team_id}`);
      const data = await res.json();
      setMatchStats(prev => ({ ...prev, [fixture.id]: data }));
      setExpandedStatsId(fixture.id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingStats(prev => ({ ...prev, [fixture.id]: false }));
    }
  };

  // Generate Knockout Bracket from Groups
  const generateBracketFromGroups = () => {
    // 1. Get 1sts and 2nds
    const firsts = groups.map(g => g.teams[0]);
    const seconds = groups.map(g => g.teams[1]);
    
    // 2. Mathematically calculate best 3rds
    const allThirds = groups.map(g => g.teams[2]);
    allThirds.sort((a: any, b: any) => {
        if (b.pts !== a.pts) return b.pts - a.pts;
        if (b.gd !== a.gd) return b.gd - a.gd;
        return b.gf - a.gf;
    });
    const bestThirds = allThirds.slice(0, 8);
    
    // Seed and pair up
    const seeded = [...firsts, ...seconds.slice(0, 4)];
    const unseeded = [...seconds.slice(4), ...bestThirds];
    
    const newBracket = generateInitialBracket();
    for (let i = 0; i < 16; i++) {
      newBracket[`R32-${i+1}`].home_team = seeded[i];
      newBracket[`R32-${i+1}`].away_team = unseeded[15 - i];
    }
    setBracket(newBracket);
    setActiveTab('bracket');
  };

  // Simulate a single bracket match
  const simulateBracketMatch = async (matchId: string, currentBracket: Record<string, BracketMatch>) => {
    const match = currentBracket[matchId];
    if (!match.home_team || !match.away_team || match.winner) return currentBracket;
    
    setSimulatingBracket(matchId);
    try {
      const res = await fetch(`/api/worldcup/predict/${match.home_team.apiId}/${match.away_team.apiId}`);
      const data = await res.json();
      
      const topScores = Object.entries(data.correct_score_top5);
      if (!topScores || topScores.length === 0) return currentBracket;
      
      let mostLikelyScoreStr = topScores[0][0] as string;
      let [homeScore, awayScore] = mostLikelyScoreStr.split('-').map(Number);
      let winner: 'home' | 'away' = homeScore > awayScore ? 'home' : (awayScore > homeScore ? 'away' : 'home'); // Default to home if tie logic fails
      
      // Knockouts can't tie, use 1X2 odds to decide penalty winner
      if (homeScore === awayScore) {
         const pHome = data['1x2'].home_win || 0;
         const pAway = data['1x2'].away_win || 0;
         winner = pHome >= pAway ? 'home' : 'away';
         if (winner === 'home') homeScore += 1; else awayScore += 1;
      }
      
      const newB = { ...currentBracket };
      newB[matchId] = { ...newB[matchId], home_score: homeScore, away_score: awayScore, winner };
      
      // Advance winner
      const nextId = newB[matchId].nextMatchId;
      if (nextId) {
          const advancingTeam = winner === 'home' ? match.home_team : match.away_team;
          newB[nextId] = { ...newB[nextId] };
          if (newB[matchId].isHomeNext) {
              newB[nextId].home_team = advancingTeam;
          } else {
              newB[nextId].away_team = advancingTeam;
          }
      }
      return newB;
    } catch (e) {
      console.error(e);
      return currentBracket;
    } finally {
      setSimulatingBracket(null);
    }
  };

  const handleSimulateSingle = async (matchId: string) => {
    const newBracket = await simulateBracketMatch(matchId, bracket);
    setBracket(newBracket);
  };

  const handleSimulateAll = async () => {
    setSimulatingAll(true);
    let currentB = { ...bracket };
    const rounds = ['R32', 'R16', 'QF', 'SF', 'F'];
    
    for (const r of rounds) {
      const matchIds = Object.keys(currentB).filter(k => k.startsWith(r + '-'));
      for (const id of matchIds) {
        if (currentB[id].home_team && currentB[id].away_team && !currentB[id].winner) {
          currentB = await simulateBracketMatch(id, currentB);
          setBracket(currentB); // Update UI progressively
          await new Promise(res => setTimeout(res, 200)); // Visual delay
        }
      }
    }
    setSimulatingAll(false);
  };

  useEffect(() => {
    if (activeTab === 'fixtures') { fetchFixtures(); fetchPredictions(); }
    if (activeTab === 'predictions') { fetchPredictions(); }
  }, [activeTab]);

  const syncProgress = syncStatus ? Math.round((syncStatus.processed / Math.max(syncStatus.total, 1)) * 100) : 0;

  // Find team flag by name
  const getFlag = (name: string): string => {
    for (const g of worldCupGroups) {
      const t = g.teams.find(t => t.name === name || name.includes(t.name) || t.name.includes(name));
      if (t) return t.flag;
    }
    return '🏳️';
  };

  const existingPredictionMap = useMemo(() => {
    const map: Record<number, Prediction> = {};
    predictions.forEach(p => { map[p.fixture_id] = p; });
    return map;
  }, [predictions]);

  const tabs = [
    { id: 'groups' as const, label: 'Fase de Grupos', icon: Trophy },
    { id: 'bracket' as const, label: 'Simulador Eliminatorias', icon: Zap },
    { id: 'fixtures' as const, label: 'Partidos & Pronósticos', icon: Swords },
    { id: 'predictions' as const, label: 'Mis Puntos', icon: BarChart3 },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-[#d4af37] to-[#f3e5ab] flex items-center gap-3">
            <Trophy className="w-8 h-8 text-[#d4af37]" /> Copa Mundial 2026
          </h2>
          <p className="text-slate-400 mt-2">Simulador, pronósticos y polla mundialista</p>
        </div>
        
        <Button
          onClick={startSync}
          disabled={syncing}
          className="bg-gradient-to-r from-[#d4af37] to-[#b8941f] hover:from-[#e5c040] hover:to-[#c9a520] text-black font-bold"
        >
          {syncing ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
          {syncing ? 'Descargando...' : '⚡ Descargar Data del Mundial'}
        </Button>
      </div>

      {/* Sync Progress Bar */}
      {syncStatus && (syncStatus.running || syncStatus.processed > 0) && (
        <Card className="bg-slate-900/80 border-slate-800">
          <CardContent className="py-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300">
                {syncStatus.running ? `Descargando: ${syncStatus.current_team}` : '✅ Sincronización completada'}
              </span>
              <span className="text-[#d4af37] font-mono font-bold">{syncProgress}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#d4af37] to-[#f3e5ab] transition-all duration-500"
                style={{ width: `${syncProgress}%` }}
              />
            </div>
            <p className="text-xs text-slate-500 mt-2">{syncStatus.processed} / {syncStatus.total} equipos procesados</p>
            {syncStatus.errors.length > 0 && (
              <p className="text-xs text-red-400 mt-1">⚠️ {syncStatus.errors.length} errores</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
              activeTab === tab.id
                ? 'bg-[#d4af37]/20 text-[#f3e5ab] shadow-[inset_0_0_10px_rgba(212,175,55,0.2)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: Fase de Grupos */}
      {activeTab === 'groups' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-xl font-bold text-[#f3e5ab]">Posiciones y Simulación</h3>
              <p className="text-sm text-slate-400">Genera los resultados usando distribución de Poisson</p>
            </div>
            
            {simulatingGroupsProgress ? (
              <div className="flex-1 w-full max-w-md bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="flex justify-between text-xs mb-1 text-slate-400">
                  <span>{simulatingGroupsProgress.message}</span>
                  <span>{Math.round((simulatingGroupsProgress.current / simulatingGroupsProgress.total) * 100)}%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-300 ease-out" 
                    style={{ width: `${(simulatingGroupsProgress.current / simulatingGroupsProgress.total) * 100}%` }}
                  />
                </div>
              </div>
            ) : (
              <div className="flex gap-3">
                <Button onClick={simulateGroupStage} className="bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_15px_rgba(79,70,229,0.3)]">
                  <Zap className="w-4 h-4 mr-2" />
                  Simular Todos los Grupos
                </Button>
                <Button onClick={generateBracketFromGroups} className="bg-green-600 hover:bg-green-500 text-white shadow-[0_0_15px_rgba(34,197,94,0.3)]">
                  <Trophy className="w-4 h-4 mr-2" />
                  Continuar a Bracket
                </Button>
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {groups.map((group) => (
            <Card key={group.name} className="bg-gradient-to-b from-slate-900 to-slate-950 border-slate-800 shadow-xl overflow-hidden hover:border-[#d4af37]/30 transition-colors">
              <CardHeader className="bg-slate-950/50 border-b border-slate-800/50 py-3">
                <CardTitle className="text-lg text-center text-[#d4af37] font-bold tracking-widest uppercase">{group.name}</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900 text-slate-400">
                    <tr>
                      <th className="px-2 py-2 w-8">#</th>
                      <th className="px-2 py-2">País</th>
                      <th className="px-1 py-2 text-center" title="Partidos Jugados">PJ</th>
                      <th className="px-1 py-2 text-center" title="Diferencia de Goles">DG</th>
                      <th className="px-2 py-2 text-center font-bold text-slate-200">PTS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.teams.map((team, tIndex) => (
                      <tr key={team.name} className={`border-b border-slate-800/30 ${tIndex < 2 ? 'bg-green-900/10' : tIndex === 2 ? 'bg-yellow-900/10' : 'opacity-60'}`}>
                        <td className="px-2 py-2 text-slate-500 font-mono text-center">{tIndex + 1}</td>
                        <td className="px-2 py-2 font-medium flex items-center gap-2 truncate">
                          <span className="text-xl">{team.flag}</span> <span className="truncate">{team.name}</span>
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
    )}

      {/* TAB 2: Fixtures & Predictions */}
      {activeTab === 'fixtures' && (
        <div className="space-y-4">
          {loadingFixtures ? (
            <div className="flex justify-center py-12"><RefreshCw className="w-8 h-8 animate-spin text-[#d4af37]" /></div>
          ) : fixtures.length === 0 ? (
            <Card className="bg-slate-900 border-slate-800 border-dashed p-12 text-center">
              <Swords className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-slate-300">No hay partidos del Mundial en la base de datos</h3>
              <p className="text-slate-500 mt-2">Presiona "⚡ Descargar Data del Mundial" para sincronizar los fixtures oficiales desde API-Football.</p>
            </Card>
          ) : (
            <>
              <div className="flex justify-between items-center">
                <p className="text-sm text-slate-400">{fixtures.length} partidos del Mundial 2026</p>
                <Badge variant="outline" className="text-[#d4af37] border-[#d4af37]/30 bg-[#d4af37]/5">
                  {predictions.length} predicciones guardadas
                </Badge>
              </div>
              
              <div className="grid gap-3">
                {fixtures.map(f => {
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
                                type="number"
                                min="0"
                                max="20"
                                value={input.home}
                                onChange={e => setScoreInputs(prev => ({ ...prev, [f.id]: { ...prev[f.id], home: e.target.value, away: prev[f.id]?.away || '' } }))}
                                className="w-10 h-8 text-center rounded-md bg-slate-800 border border-slate-700 text-white text-sm font-mono focus:border-[#d4af37] focus:outline-none"
                                placeholder="-"
                              />
                              <span className="text-slate-500 font-bold">-</span>
                              <input
                                type="number"
                                min="0"
                                max="20"
                                value={input.away}
                                onChange={e => setScoreInputs(prev => ({ ...prev, [f.id]: { home: prev[f.id]?.home || '', away: e.target.value } }))}
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
                              onClick={() => loadMatchStats(f)}
                              disabled={loadingStats[f.id]}
                              variant="outline"
                              className="text-xs px-2 h-8 bg-slate-800 border-slate-700 hover:bg-slate-700"
                              title="Ver Probabilidades"
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

                      {/* Probabilities Expansion */}
                      {expandedStatsId === f.id && matchStats[f.id] && (
                        <div className="bg-slate-950 border-t border-slate-800 p-4 animate-in slide-in-from-top-2">
                          <div className="flex flex-col md:flex-row gap-6">
                            {/* Correct Score Probabilities */}
                            <div className="flex-1">
                              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Marcadores Más Probables</h4>
                              <div className="space-y-2">
                                {Object.entries(matchStats[f.id]?.correct_score_top5 || {}).map(([score, prob]: [string, any]) => (
                                  <div key={score} className="flex items-center gap-3 text-sm">
                                    <span className="font-mono font-bold text-[#f3e5ab] w-12 text-right">{score}</span>
                                    <div className="flex-grow bg-slate-800 rounded-full h-2 overflow-hidden">
                                      <div 
                                        className="bg-blue-500 h-full rounded-full" 
                                        style={{ width: `${Math.min(prob * 100 * 3, 100)}%` }} // *3 just to make bars visible, Poisson exact scores are usually < 15%
                                      />
                                    </div>
                                    <span className="font-mono text-slate-300 w-12">{(prob * 100).toFixed(1)}%</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                            
                            {/* Match Odds 1X2 */}
                            <div className="flex-1">
                              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Probabilidad de Ganar (1X2)</h4>
                              <div className="grid grid-cols-3 gap-2">
                                <div className="bg-slate-800 p-3 rounded-lg text-center relative overflow-hidden">
                                  <div className="absolute top-0 right-0 bg-slate-700/50 text-[10px] px-1.5 py-0.5 rounded-bl-lg font-mono text-[#d4af37]">
                                    ★ {matchStats[f.id]?.squad_rating?.home || "6.5"}
                                  </div>
                                  <div className="text-xs text-slate-400 mb-1">{f.home_team_name}</div>
                                  <div className="font-bold text-green-400">{(matchStats[f.id]?.['1x2']?.home_win * 100 || 0).toFixed(1)}%</div>
                                </div>
                                <div className="bg-slate-800 p-3 rounded-lg text-center border border-slate-700">
                                  <div className="text-xs text-slate-400 mb-1">Empate</div>
                                  <div className="font-bold text-yellow-400">{(matchStats[f.id]?.['1x2']?.draw * 100 || 0).toFixed(1)}%</div>
                                </div>
                                <div className="bg-slate-800 p-3 rounded-lg text-center relative overflow-hidden">
                                  <div className="absolute top-0 right-0 bg-slate-700/50 text-[10px] px-1.5 py-0.5 rounded-bl-lg font-mono text-[#d4af37]">
                                    ★ {matchStats[f.id]?.squad_rating?.away || "6.5"}
                                  </div>
                                  <div className="text-xs text-slate-400 mb-1">{f.away_team_name}</div>
                                  <div className="font-bold text-blue-400">{(matchStats[f.id]?.['1x2']?.away_win * 100 || 0).toFixed(1)}%</div>
                                </div>
                              </div>
                              <p className="text-xs text-slate-500 mt-3 text-center">
                                Basado en el historial de los últimos 20 partidos mediante distribución de Poisson.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </Card>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}

      {/* TAB 3: My Points */}
      {activeTab === 'predictions' && (
        <div className="space-y-6">
          {/* Points Summary */}
          <Card className="bg-gradient-to-r from-[#d4af37]/10 to-transparent border-[#d4af37]/30">
            <CardContent className="py-6 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-[#f3e5ab]">Total de Puntos</h3>
                <p className="text-slate-400 text-sm mt-1">{predictions.length} predicciones realizadas</p>
              </div>
              <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-[#d4af37] to-[#f3e5ab]">
                {totalPoints}
              </div>
            </CardContent>
          </Card>

          {/* Scoring Rules */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-slate-400 uppercase tracking-widest">Sistema de Puntos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
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

          {/* Predictions Table */}
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
                    {predictions.map(p => (
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
      )}
      {/* TAB 4: Bracket Simulator */}
      {activeTab === 'bracket' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <div>
              <h3 className="text-xl font-bold text-[#f3e5ab]">Árbol de Eliminatorias</h3>
              <p className="text-sm text-slate-400">Simula la fase final usando el motor probabilístico de Poisson</p>
            </div>
            <div className="flex gap-3">
              <Button onClick={generateBracketFromGroups} variant="outline" className="border-slate-700 hover:bg-slate-800">
                <RefreshCw className="w-4 h-4 mr-2" /> Reiniciar
              </Button>
              <Button onClick={handleSimulateAll} disabled={simulatingAll} className="bg-[#d4af37] hover:bg-[#c9a520] text-black font-bold shadow-[0_0_15px_rgba(212,175,55,0.4)]">
                {simulatingAll ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
                Simular Todo
              </Button>
            </div>
          </div>

          <div className="overflow-x-auto pb-8">
            <div className="flex gap-8 min-w-max px-4">
              {/* Bracket Columns */}
              {['R32', 'R16', 'QF', 'SF', 'F'].map((round, colIndex) => {
                const roundMatches = Object.values(bracket).filter(m => m.round === round);
                return (
                  <div key={round} className="flex flex-col justify-around gap-4" style={{ width: '220px' }}>
                    <div className="text-center font-bold text-slate-500 mb-4 uppercase tracking-widest text-xs">
                      {round === 'R32' ? 'Dieciseisavos' : round === 'R16' ? 'Octavos' : round === 'QF' ? 'Cuartos' : round === 'SF' ? 'Semifinal' : 'Final'}
                    </div>
                    {roundMatches.map(m => (
                      <div key={m.id} className="relative">
                        <Card className={`bg-slate-900 border ${m.winner ? 'border-[#d4af37]/50 shadow-[0_0_10px_rgba(212,175,55,0.1)]' : 'border-slate-800'} overflow-hidden relative z-10`}>
                          <div className="flex flex-col text-sm">
                            {/* Home Team */}
                            <div className={`flex items-center justify-between p-2 border-b border-slate-800/50 ${m.winner === 'home' ? 'bg-[#d4af37]/10' : ''}`}>
                              <div className="flex items-center gap-2 truncate">
                                <span>{m.home_team ? getFlag(m.home_team.name) : '🏳️'}</span>
                                <span className={`truncate ${m.winner === 'away' ? 'text-slate-500 line-through' : 'text-slate-200'}`}>{m.home_team ? m.home_team.name : 'TBD'}</span>
                              </div>
                              <span className={`font-mono font-bold ${m.winner === 'home' ? 'text-[#d4af37]' : 'text-slate-400'}`}>{m.home_score !== null ? m.home_score : '-'}</span>
                            </div>
                            {/* Away Team */}
                            <div className={`flex items-center justify-between p-2 ${m.winner === 'away' ? 'bg-[#d4af37]/10' : ''}`}>
                              <div className="flex items-center gap-2 truncate">
                                <span>{m.away_team ? getFlag(m.away_team.name) : '🏳️'}</span>
                                <span className={`truncate ${m.winner === 'home' ? 'text-slate-500 line-through' : 'text-slate-200'}`}>{m.away_team ? m.away_team.name : 'TBD'}</span>
                              </div>
                              <span className={`font-mono font-bold ${m.winner === 'away' ? 'text-[#d4af37]' : 'text-slate-400'}`}>{m.away_score !== null ? m.away_score : '-'}</span>
                            </div>
                          </div>
                          
                          {/* Simulate Overlay Button */}
                          {!m.winner && m.home_team && m.away_team && (
                            <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-[1px] flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                              <Button size="sm" onClick={() => handleSimulateSingle(m.id)} disabled={simulatingBracket === m.id} className="bg-[#d4af37]/20 hover:bg-[#d4af37]/40 text-[#d4af37] border border-[#d4af37]/50 h-8 text-xs">
                                {simulatingBracket === m.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Simular'}
                              </Button>
                            </div>
                          )}
                        </Card>
                        
                        {/* Connector Lines (Visual) */}
                        {colIndex < 4 && (
                           <div className="absolute top-1/2 -right-4 w-4 border-t-2 border-slate-700 z-0" />
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
                        <div className="text-4xl mb-2">{getFlag(bracket['F-1'][`${bracket['F-1'].winner}_team`].name)}</div>
                        <h2 className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-[#d4af37] to-[#f3e5ab] uppercase">
                          {bracket['F-1'][`${bracket['F-1'].winner}_team`].name}
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
      )}
    </div>
  );
}
