import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Search, UserCircle2, Activity } from 'lucide-react';

export default function PlayerBrowserView() {
  const [players, setPlayers] = useState([]);
  const [leagues, setLeagues] = useState([]);
  const [teams, setTeams] = useState([]);
  
  const [selectedLeague, setSelectedLeague] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Cargar ligas y equipos iniciales (se simplifica reusando el endpoint de stats)
    fetch('/api/database/stats').then(r => r.json()).then(data => setLeagues(data.leagues || []));
    fetch('/api/teams').then(r => r.json()).then(data => setTeams(data || []));
  }, []);

  useEffect(() => {
    const fetchPlayers = async () => {
      setLoading(true);
      try {
        let url = `/api/players?limit=100`;
        if (selectedLeague) url += `&league_id=${selectedLeague}`;
        if (selectedTeam) url += `&team_id=${selectedTeam}`;
        if (search) url += `&search=${search}`;
        
        const res = await fetch(url);
        const data = await res.json();
        setPlayers(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    
    // Debounce search
    const timer = setTimeout(fetchPlayers, 300);
    return () => clearTimeout(timer);
  }, [selectedLeague, selectedTeam, search]);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <UserCircle2 className="w-8 h-8 text-yellow-500" /> Explorador de Jugadores
        </h2>
        <p className="text-slate-400 mt-2">Filtra y busca jugadores en la base de datos SQL</p>
      </div>

      <Card className="bg-slate-900 border-slate-800">
        <CardContent className="pt-6">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Liga</label>
              <select 
                className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                value={selectedLeague} onChange={e => setSelectedLeague(e.target.value)}
              >
                <option value="">Todas las ligas</option>
                {leagues.map((l: any) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Equipo</label>
              <select 
                className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                value={selectedTeam} onChange={e => setSelectedTeam(e.target.value)}
              >
                <option value="">Todos los equipos</option>
                {teams.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Buscar por nombre</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-500" />
                <input 
                  type="text" 
                  placeholder="Ej. Lionel Messi" 
                  className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-8 py-2 text-sm text-slate-100"
                  value={search} onChange={e => setSearch(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900 border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 uppercase bg-slate-950 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Jugador</th>
                <th className="px-6 py-4">Posición</th>
                <th className="px-6 py-4">Equipo</th>
                <th className="px-6 py-4">Nacionalidad</th>
                <th className="px-6 py-4">Edad</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500"><Activity className="w-6 h-6 animate-spin mx-auto" /></td></tr>
              ) : players.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500">No se encontraron jugadores</td></tr>
              ) : (
                players.map((p: any) => (
                  <tr key={p.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                    <td className="px-6 py-4 font-medium text-slate-200">{p.name}</td>
                    <td className="px-6 py-4"><Badge variant="outline" className="bg-slate-950">{p.position}</Badge></td>
                    <td className="px-6 py-4 text-slate-300">{p.team_name}</td>
                    <td className="px-6 py-4 text-slate-400">{p.nationality || '-'}</td>
                    <td className="px-6 py-4 text-slate-400">{p.age || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
