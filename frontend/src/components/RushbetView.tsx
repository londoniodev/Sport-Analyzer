import { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Activity, Clock, TrendingUp } from 'lucide-react';

export default function RushbetView() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/rushbet');
      const data = await res.json();
      setEvents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-8 h-8 text-green-500" /> Eventos en Vivo Rushbet
          </h2>
          <p className="text-slate-400 mt-2">Cuotas reales de Kambi/Rushbet sincronizadas al instante</p>
        </div>
        <Button onClick={fetchEvents} disabled={loading} className="bg-green-600 hover:bg-green-700">
          {loading ? <Activity className="w-4 h-4 mr-2 animate-spin" /> : <Activity className="w-4 h-4 mr-2" />}
          Cargar Eventos
        </Button>
      </div>

      <Card className="bg-slate-900 border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 uppercase bg-slate-950 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Hora</th>
                <th className="px-6 py-4">Liga</th>
                <th className="px-6 py-4">Partido</th>
                <th className="px-6 py-4 text-center">1</th>
                <th className="px-6 py-4 text-center">X</th>
                <th className="px-6 py-4 text-center">2</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500"><Activity className="w-6 h-6 animate-spin mx-auto" /></td></tr>
              ) : events.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">Presiona "Cargar Eventos" para iniciar el web scraper.</td></tr>
              ) : (
                events.map((e: any, i) => (
                  <tr key={e.id || i} className="border-b border-slate-800 hover:bg-slate-800/50">
                    <td className="px-6 py-4 text-slate-400 flex items-center gap-2">
                      <Clock className="w-3 h-3" /> {new Date(e.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </td>
                    <td className="px-6 py-4"><span className="text-slate-400 text-xs">{e.league}</span></td>
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-200">{e.home_team}</div>
                      <div className="font-bold text-slate-300 mt-1">{e.away_team}</div>
                    </td>
                    <td className="px-6 py-4 text-center font-mono text-green-400">{e.odds_1?.toFixed(2) || '-'}</td>
                    <td className="px-6 py-4 text-center font-mono text-yellow-400">{e.odds_x?.toFixed(2) || '-'}</td>
                    <td className="px-6 py-4 text-center font-mono text-red-400">{e.odds_2?.toFixed(2) || '-'}</td>
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
