import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Database, Users, Trophy, Activity, RefreshCw, Layers } from 'lucide-react';

export default function DashboardView() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  
  // Sync form states
  const [selectedLeague, setSelectedLeague] = useState('');
  const [selectedSeason, setSelectedSeason] = useState('2024');
  const [syncDetails, setSyncDetails] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/database/stats');
      const data = await res.json();
      setStats(data);
      if (data.leagues && data.leagues.length > 0) {
        setSelectedLeague(data.leagues[0].id.toString());
      }
    } catch (error) {
      console.error("Failed to fetch stats", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    if (!selectedLeague) return;
    setSyncing(true);
    try {
      await fetch('/api/etl/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          league_id: parseInt(selectedLeague),
          season: parseInt(selectedSeason),
          sync_details: syncDetails
        })
      });
      alert('Sincronización iniciada en segundo plano. Los datos se actualizarán pronto.');
    } catch (error) {
      alert('Error iniciando la sincronización');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><RefreshCw className="w-8 h-8 animate-spin text-blue-500" /></div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Activity className="w-8 h-8 text-blue-500" /> Panel de Control
        </h2>
        <p className="text-slate-400 mt-2">Gestión de datos, sincronización y estado del sistema</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Partidos</CardTitle>
            <Database className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-100">{stats?.counts?.fixtures || 0}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Equipos</CardTitle>
            <Users className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-100">{stats?.counts?.teams || 0}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Jugadores</CardTitle>
            <Users className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-100">{stats?.counts?.players || 0}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Ligas</CardTitle>
            <Trophy className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-100">{stats?.counts?.leagues || 0}</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Lesiones</CardTitle>
            <Activity className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-100">{stats?.counts?.injuries || 0}</div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 shadow-xl backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-slate-100">
            <Layers className="w-5 h-5 text-purple-400" /> Sincronización de Datos (ETL)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-slate-400">Competición</label>
              <select 
                className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100 ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={selectedLeague}
                onChange={(e) => setSelectedLeague(e.target.value)}
              >
                {stats?.leagues?.map((l: any) => (
                  <option key={l.id} value={l.id}>{l.name} ({l.country})</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Temporada</label>
              <select 
                className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100 ring-offset-background"
                value={selectedSeason}
                onChange={(e) => setSelectedSeason(e.target.value)}
              >
                {[2026, 2025, 2024, 2023, 2022].map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="mt-4 flex items-center gap-2">
            <input 
              type="checkbox" 
              id="details" 
              checked={syncDetails}
              onChange={(e) => setSyncDetails(e.target.checked)}
              className="rounded border-slate-800 bg-slate-950" 
            />
            <label htmlFor="details" className="text-sm text-slate-400">Incluir Detalles (Alineaciones y stats de jugadores)</label>
          </div>

          <div className="mt-6 flex gap-4">
            <Button onClick={handleSync} disabled={syncing} className="bg-blue-600 hover:bg-blue-700 text-white">
              {syncing ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Database className="w-4 h-4 mr-2" />}
              Sincronizar Liga
            </Button>
            <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
              Sync Prioritarias (Batch)
            </Button>
            <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
              Actualizar Lesiones
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
