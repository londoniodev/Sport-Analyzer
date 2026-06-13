import { useState } from 'react';
import { worldCupGroups } from '../lib/worldCupData';
import type { SyncStatus, WCFixture, Prediction, BracketMatch } from '../components/worldcup/types';
import { generateInitialBracket, getWeightedRandomScore } from '../components/worldcup/utils';

export function useWorldCup() {
  const [activeTab, setActiveTab] = useState<'groups' | 'fixtures' | 'predictions' | 'bracket'>('groups');
  
  // Data Sync State
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);

  // Group Simulation State
  const [groups, setGroups] = useState(() => 
    worldCupGroups.map((g: any) => ({
      ...g,
      teams: g.teams.map((t: any) => ({ ...t, played: 0, pts: 0, gf: 0, ga: 0, gd: 0 })),
      matches: []
    }))
  );
  const [simulatingGroupsProgress, setSimulatingGroupsProgress] = useState<{current: number, total: number, message: string} | null>(null);

  // Fixtures State
  const [fixtures, setFixtures] = useState<WCFixture[]>([]);
  const [loadingFixtures, setLoadingFixtures] = useState(false);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [totalPoints, setTotalPoints] = useState(0);
  const [scoreInputs, setScoreInputs] = useState<Record<number, {home: string, away: string}>>({});
  const [savingId, setSavingId] = useState<number | null>(null);

  // Advanced Stats & Modal State
  const [matchStats, setMatchStats] = useState<Record<string, any>>({});
  const [loadingStats, setLoadingStats] = useState<Record<string, boolean>>({});
  const [selectedMatchModal, setSelectedMatchModal] = useState<{ id: string | number, homeId: number, awayId: number, homeName: string, awayName: string } | null>(null);

  // Bracket State
  const [bracket, setBracket] = useState<Record<string, BracketMatch>>(generateInitialBracket());
  const [simulatingBracket, setSimulatingBracket] = useState<string | null>(null);
  const [simulatingAll, setSimulatingAll] = useState(false);
  const [bracketZoom, setBracketZoom] = useState(0.8);

  // --- ACTIONS ---

  const startSync = async () => {
    setSyncing(true);
    setSyncStatus({ running: true, total: 48, processed: 0, current_team: 'Iniciando...', errors: [] });
    try {
      const res = await fetch('/api/worldcup/sync', { method: 'POST' });
      if (!res.ok) throw new Error('Sync failed');
      const interval = setInterval(async () => {
        const statRes = await fetch('/api/worldcup/sync/status');
        const status = await statRes.json();
        setSyncStatus(status);
        if (!status.running) {
          clearInterval(interval);
          setSyncing(false);
        }
      }, 1000);
    } catch (e) {
      console.error(e);
      setSyncing(false);
    }
  };

  const startDataSync = async () => {
    try {
      alert("Iniciando sincronización de plantillas (Wikipedia) y puntos Elo. Esto ocurrirá en segundo plano en el servidor.");
      const res = await fetch('/api/worldcup/sync-data', { method: 'POST' });
      const data = await res.json();
      console.log(data);
    } catch (e) {
      console.error(e);
      alert("Error al intentar sincronizar los datos.");
    }
  };

  const simulateGroupStage = async () => {
    setSimulatingGroupsProgress({ current: 0, total: 72, message: 'Preparando calendarios...' });
    
    // Always start from a clean copy of worldCupGroups to avoid index shifts from previous sortings
    const updatedGroups = worldCupGroups.map((g: any) => ({
      ...g,
      teams: g.teams.map((t: any) => ({ ...t, played: 0, pts: 0, gf: 0, ga: 0, gd: 0 })),
      matches: []
    }));
    
    let matchesSimulated = 0;
    const matchPairs = [[0,1], [2,3], [0,2], [1,3], [0,3], [1,2]];
    
    for (let gIndex = 0; gIndex < 12; gIndex++) {
       const group = updatedGroups[gIndex];
       group.matches = [];
       for (const pair of matchPairs) {
           const teamHome = group.teams[pair[0]];
           const teamAway = group.teams[pair[1]];
           if (!teamHome || !teamAway) continue;
           
           setSimulatingGroupsProgress({ current: matchesSimulated, total: 72, message: `Simulando: ${teamHome.name} vs ${teamAway.name}` });
           try {
               const res = await fetch(`/api/worldcup/predict/${teamHome.apiId}/${teamAway.apiId}`);
               const data = await res.json();
               if (data.polla_score) {
                   const homeScore = data.polla_score.home;
                   const awayScore = data.polla_score.away;
                   
                   group.matches.push({
                       home: teamHome.name,
                       homeFlag: teamHome.flag,
                       away: teamAway.name,
                       awayFlag: teamAway.flag,
                       homeScore,
                       awayScore
                   });

                   teamHome.played += 1;
                   teamAway.played += 1;
                   teamHome.gf += homeScore;
                   teamHome.ga += awayScore;
                   teamHome.gd = teamHome.gf - teamHome.ga;
                   
                   teamAway.gf += awayScore;
                   teamAway.ga += homeScore;
                   teamAway.gd = teamAway.gf - teamAway.ga;
                   
                   if (homeScore > awayScore) teamHome.pts += 3;
                   else if (awayScore > homeScore) teamAway.pts += 3;
                   else { teamHome.pts += 1; teamAway.pts += 1; }
               }
           } catch (e) { console.error("Sim fail", e); }
           matchesSimulated++;
       }
       group.teams.sort((a: any, b: any) => {
           if (b.pts !== a.pts) return b.pts - a.pts;
           if (b.gd !== a.gd) return b.gd - a.gd;
           return b.gf - a.gf;
       });
       setGroups([...updatedGroups]); 
    }
    setSimulatingGroupsProgress(null);
  };

  const loadFixtures = async () => {
    setLoadingFixtures(true);
    try {
      const res = await fetch('/api/worldcup/fixtures');
      const data = await res.json();
      setFixtures(data);
    } catch (e) { console.error(e); }
    finally { setLoadingFixtures(false); }
  };

  const fetchPredictions = async () => {
    try {
      const res = await fetch('/api/worldcup/predictions');
      const data = await res.json();
      setPredictions(data.predictions || []);
      setTotalPoints(data.total_points || 0);
      const inputs: Record<number, {home: string, away: string}> = {};
      for (const p of data.predictions || []) {
        inputs[p.fixture_id] = { home: String(p.predicted_home), away: String(p.predicted_away) };
      }
      setScoreInputs(prev => ({ ...inputs, ...prev }));
    } catch (e) { console.error(e); }
  };

  const savePrediction = async (fixtureId: number) => {
    const input = scoreInputs[fixtureId];
    if (!input || input.home === '' || input.away === '') return;
    setSavingId(fixtureId);
    try {
      await fetch('/api/worldcup/predict-score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fixture_id: fixtureId, predicted_home_score: parseInt(input.home), predicted_away_score: parseInt(input.away) })
      });
      fetchPredictions();
    } catch (e) { console.error(e); }
    finally { setSavingId(null); }
  };

  const openMatchStatsModal = async (matchId: string | number, homeId: number, awayId: number, homeName: string, awayName: string) => {
    setSelectedMatchModal({ id: matchId, homeId, awayId, homeName, awayName });
    if (matchStats[matchId]) return;
    setLoadingStats(prev => ({ ...prev, [matchId]: true }));
    try {
      const res = await fetch(`/api/worldcup/predict/${homeId}/${awayId}`);
      const data = await res.json();
      setMatchStats(prev => ({ ...prev, [matchId]: data }));
    } catch (e) { console.error(e); }
    finally { setLoadingStats(prev => ({ ...prev, [matchId]: false })); }
  };

  const generateBracketFromGroups = () => {
    const firsts = groups.map((g: any) => g.teams[0]);
    const seconds = groups.map((g: any) => g.teams[1]);
    const allThirds = groups.map((g: any) => g.teams[2]);
    allThirds.sort((a: any, b: any) => {
        if (b.pts !== a.pts) return b.pts - a.pts;
        if (b.gd !== a.gd) return b.gd - a.gd;
        return b.gf - a.gf;
    });
    const bestThirds = allThirds.slice(0, 8);
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

  const simulateBracketMatch = async (matchId: string, currentBracket: Record<string, BracketMatch>) => {
    const match = currentBracket[matchId];
    if (!match.home_team || !match.away_team || match.winner) return currentBracket;
    setSimulatingBracket(matchId);
    try {
      const res = await fetch(`/api/worldcup/predict/${match.home_team.apiId}/${match.away_team.apiId}`);
      const data = await res.json();
      
      if (data.polla_score) {
        const homeScore = data.polla_score.home;
        const awayScore = data.polla_score.away;
        const isDraw = homeScore === awayScore;
        const penaltyQualifier = isDraw ? data.penalty_qualifier : null;
        const winner = isDraw ? penaltyQualifier : (homeScore > awayScore ? 'home' : 'away');
        const winningTeam = winner === 'home' ? match.home_team : match.away_team;
        
        currentBracket[matchId] = { 
          ...match, 
          home_score: homeScore, 
          away_score: awayScore, 
          polla_score: data.polla_score,
          is_draw_90: isDraw,
          penalty_qualifier: penaltyQualifier,
          winner,
          montecarlo: data.montecarlo
        };
        
        if (match.nextMatchId && currentBracket[match.nextMatchId]) {
          const nextMatch = currentBracket[match.nextMatchId];
          if (match.isHomeNext) nextMatch.home_team = winningTeam;
          else nextMatch.away_team = winningTeam;
        }
      }
    } catch (e) { console.error(e); }
    finally { setSimulatingBracket(null); }
    return currentBracket;
  };

  const runMontecarlo = async (matchId: string) => {
    const match = bracket[matchId];
    if (!match.home_team || !match.away_team) return;
    setSimulatingBracket(matchId); // Reuse this state for the spinner
    try {
      const res = await fetch('/api/worldcup/simulate/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ home_id: match.home_team.apiId, away_id: match.away_team.apiId, simulations: 10000 })
      });
      const data = await res.json();
      setBracket(prev => ({
        ...prev,
        [matchId]: {
          ...prev[matchId],
          montecarlo: data
        }
      }));
    } catch (e) { console.error(e); }
    finally { setSimulatingBracket(null); }
  };

  const exportPolla = () => {
    // Generate a simple JSON containing group matches and bracket predictions
    const exportData: any = { groups: [], bracket: [] };
    
    groups.forEach((g: any) => {
      g.matches.forEach((m: any) => {
        exportData.groups.push({ home: m.home, away: m.away, score: `${m.homeScore}-${m.awayScore}` });
      });
    });

    Object.values(bracket).forEach(m => {
      if (m.home_team && m.away_team && m.polla_score) {
        exportData.bracket.push({
          round: m.round,
          home: m.home_team.name,
          away: m.away_team.name,
          score: `${m.polla_score.home}-${m.polla_score.away}`,
          qualifier: m.penalty_qualifier ? (m.penalty_qualifier === 'home' ? m.home_team.name : m.away_team.name) : (m.polla_score.home > m.polla_score.away ? m.home_team.name : m.away_team.name)
        });
      }
    });

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'polla_optima_2026.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleSimulateSingle = async (matchId: string) => {
    const newBracket = { ...bracket };
    await simulateBracketMatch(matchId, newBracket);
    setBracket({ ...newBracket });
  };

  const handleSimulateAll = async () => {
    setSimulatingAll(true);
    let currentBracket = { ...bracket };
    const rounds = ['R32', 'R16', 'QF', 'SF', 'F'];
    for (const round of rounds) {
      const roundMatches = Object.values(currentBracket).filter(m => m.round === round);
      for (const match of roundMatches) {
        currentBracket = await simulateBracketMatch(match.id, currentBracket);
        setBracket({ ...currentBracket }); 
      }
    }
    setSimulatingAll(false);
  };

  return {
    activeTab, setActiveTab,
    syncStatus, syncing, startSync, startDataSync,
    groups, setGroups, simulatingGroupsProgress, simulateGroupStage, generateBracketFromGroups,
    fixtures, loadingFixtures, loadFixtures,
    predictions, totalPoints, fetchPredictions,
    scoreInputs, setScoreInputs, savingId, savePrediction,
    matchStats, loadingStats, openMatchStatsModal, selectedMatchModal, setSelectedMatchModal,
    bracket, setBracket, simulatingBracket, simulatingAll, bracketZoom, setBracketZoom,
    handleSimulateSingle, handleSimulateAll, runMontecarlo, exportPolla
  };
}
