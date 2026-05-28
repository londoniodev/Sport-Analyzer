import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Activity, Swords, Target, Crosshair, Flag } from 'lucide-react';

export default function PredictionsView() {
  const [teams, setTeams] = useState<any[]>([]);
  const [homeId, setHomeId] = useState('');
  const [awayId, setAwayId] = useState('');
  
  const [params, setParams] = useState({
    home_attack: 1.5, home_defense: 1.0, home_corners: 5.0, home_corners_conceded: 4.5, home_cards: 2.0, home_shots: 12.0,
    away_attack: 1.2, away_defense: 1.2, away_corners: 4.5, away_corners_conceded: 5.0, away_cards: 2.5, away_shots: 10.0
  });

  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('Goles y Marcador');

  useEffect(() => {
    fetch('/api/teams').then(r => r.json()).then(data => {
      setTeams(data);
      if (data.length >= 2) {
        setHomeId(data[0].id.toString());
        setAwayId(data[1].id.toString());
      }
    });
  }, []);

  useEffect(() => {
    if (homeId) fetchTeamStats(homeId, 'home');
  }, [homeId]);

  useEffect(() => {
    if (awayId) fetchTeamStats(awayId, 'away');
  }, [awayId]);

  const fetchTeamStats = async (id: string, side: 'home' | 'away') => {
    try {
      const res = await fetch(`/api/teams/${id}/stats`);
      if (res.ok) {
        const stats = await res.json();
        setParams(prev => ({
          ...prev,
          [`${side}_attack`]: stats.goals_scored_avg,
          [`${side}_defense`]: stats.goals_conceded_avg,
          [`${side}_corners`]: stats.corners_avg,
          [`${side}_corners_conceded`]: stats.corners_conceded_avg,
          [`${side}_cards`]: stats.cards_total_avg,
          [`${side}_shots`]: stats.shots_avg
        }));
      }
    } catch (e) { console.error("Error fetching stats", e); }
  };

  const updateParam = (key: string, value: string) => {
    setParams(prev => ({ ...prev, [key]: parseFloat(value) || 0 }));
  };

  const calculate = async () => {
    setLoading(true);
    try {
      const homeName = teams.find((t: any) => t.id.toString() === homeId)?.name || 'Local';
      const awayName = teams.find((t: any) => t.id.toString() === awayId)?.name || 'Visitante';
      
      const res = await fetch('/api/predict/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ home_name: homeName, away_name: awayName, ...params })
      });
      const data = await res.json();
      setPrediction(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Activity className="w-8 h-8 text-pink-500" /> Motor Predictivo Poisson
        </h2>
        <p className="text-slate-400 mt-2">Configura los parámetros estadísticos y calcula probabilidades avanzadas</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* LOCAL */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="border-b border-slate-800 pb-4">
            <CardTitle className="text-lg text-blue-400 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500"></span> Equipo Local
            </CardTitle>
            <select 
              className="mt-2 flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
              value={homeId} onChange={e => setHomeId(e.target.value)}
            >
              {teams.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Goles Anotados (Avg)</span><span>{params.home_attack.toFixed(2)}</span>
              </div>
              <input type="range" min="0.5" max="3.5" step="0.1" value={params.home_attack} onChange={e => updateParam('home_attack', e.target.value)} className="w-full accent-blue-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Goles Recibidos (Avg)</span><span>{params.home_defense.toFixed(2)}</span>
              </div>
              <input type="range" min="0.5" max="3.5" step="0.1" value={params.home_defense} onChange={e => updateParam('home_defense', e.target.value)} className="w-full accent-blue-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Córners (Avg)</span><span>{params.home_corners.toFixed(2)}</span>
              </div>
              <input type="range" min="2" max="10" step="0.5" value={params.home_corners} onChange={e => updateParam('home_corners', e.target.value)} className="w-full accent-blue-500" />
            </div>
          </CardContent>
        </Card>

        {/* VISITANTE */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="border-b border-slate-800 pb-4">
            <CardTitle className="text-lg text-red-400 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500"></span> Equipo Visitante
            </CardTitle>
            <select 
              className="mt-2 flex h-10 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
              value={awayId} onChange={e => setAwayId(e.target.value)}
            >
              {teams.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Goles Anotados (Avg)</span><span>{params.away_attack.toFixed(2)}</span>
              </div>
              <input type="range" min="0.5" max="3.5" step="0.1" value={params.away_attack} onChange={e => updateParam('away_attack', e.target.value)} className="w-full accent-red-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Goles Recibidos (Avg)</span><span>{params.away_defense.toFixed(2)}</span>
              </div>
              <input type="range" min="0.5" max="3.5" step="0.1" value={params.away_defense} onChange={e => updateParam('away_defense', e.target.value)} className="w-full accent-red-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm text-slate-400 mb-1">
                <span>Córners (Avg)</span><span>{params.away_corners.toFixed(2)}</span>
              </div>
              <input type="range" min="2" max="10" step="0.5" value={params.away_corners} onChange={e => updateParam('away_corners', e.target.value)} className="w-full accent-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Button onClick={calculate} disabled={loading} className="w-full h-12 text-lg bg-pink-600 hover:bg-pink-700 text-white font-bold">
        {loading ? <Activity className="w-5 h-5 mr-2 animate-spin" /> : <Swords className="w-5 h-5 mr-2" />}
        Calcular Probabilidades
      </Button>

      {prediction && (
        <div className="space-y-6 mt-8 animate-in slide-in-from-bottom-4 duration-500">
          <div className="grid md:grid-cols-3 gap-4">
            <Card className="bg-slate-900 border-slate-800 text-center">
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-blue-400">{(prediction['1x2'].home_win * 100).toFixed(1)}%</div>
                <div className="text-sm text-slate-400 mt-1">Gana Local (@ {(1/prediction['1x2'].home_win).toFixed(2)})</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-900 border-slate-800 text-center">
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-yellow-500">{(prediction['1x2'].draw * 100).toFixed(1)}%</div>
                <div className="text-sm text-slate-400 mt-1">Empate (@ {(1/prediction['1x2'].draw).toFixed(2)})</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-900 border-slate-800 text-center">
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-red-400">{(prediction['1x2'].away_win * 100).toFixed(1)}%</div>
                <div className="text-sm text-slate-400 mt-1">Gana Visita (@ {(1/prediction['1x2'].away_win).toFixed(2)})</div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-8 border-t border-slate-800 pt-6">
            <div className="flex gap-2 overflow-x-auto pb-4 mb-4">
              {['Goles y Marcador', 'Hándicap Asiático', 'Córners', 'Tarjetas', 'Remates'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 font-medium text-sm rounded-full transition-colors whitespace-nowrap ${
                    activeTab === tab 
                      ? 'bg-pink-600 text-white' 
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {activeTab === 'Goles y Marcador' && (
              <div className="grid md:grid-cols-2 gap-6 animate-in fade-in duration-300">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2"><Target className="w-5 h-5 text-green-500" /> Mercado de Goles</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                        <span className="text-slate-300">Ambos Marcan (BTTS)</span>
                        <Badge className="bg-green-600">{(prediction.btts.yes * 100).toFixed(1)}%</Badge>
                      </div>
                      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                        <span className="text-slate-300">Over 1.5 Goles</span>
                        <Badge variant="outline" className="text-slate-300 border-slate-700">{(prediction.over_under['1.5']?.over * 100).toFixed(1)}%</Badge>
                      </div>
                      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                        <span className="text-slate-300">Over 2.5 Goles</span>
                        <Badge variant="outline" className="text-slate-300 border-slate-700">{(prediction.over_under['2.5']?.over * 100).toFixed(1)}%</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-300">Over 3.5 Goles</span>
                        <Badge variant="outline" className="text-slate-300 border-slate-700">{(prediction.over_under['3.5']?.over * 100).toFixed(1)}%</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2"><Crosshair className="w-5 h-5 text-purple-500" /> Marcadores Probables</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-5 gap-2">
                      {Object.entries(prediction.correct_score_top5 || {}).map(([score, prob]: any) => (
                        <div key={score} className="bg-slate-950 border border-slate-800 rounded-md p-2 text-center">
                          <div className="text-lg font-bold text-slate-200">{score}</div>
                          <div className="text-xs text-slate-500">{(prob * 100).toFixed(1)}%</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'Hándicap Asiático' && (
              <Card className="bg-slate-900 border-slate-800 animate-in fade-in duration-300">
                <CardHeader>
                  <CardTitle className="text-slate-100 flex items-center gap-2">Hándicap Asiático Principal</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(prediction.handicaps?.asian_handicaps || {}).map(([line, probs]: any) => (
                      <div key={line} className="bg-slate-950 border border-slate-800 rounded p-3 flex justify-between items-center">
                        <span className="text-slate-300 font-bold">{line.replace('home_', 'L ').replace('away_', 'V ')}</span>
                        <span className="text-blue-400">{(probs.win * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === 'Córners' && (
              <div className="grid md:grid-cols-2 gap-6 animate-in fade-in duration-300">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader><CardTitle className="text-slate-100">Córners Esperados</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center"><span className="text-slate-400">Local</span><span className="text-xl font-bold">{prediction.corners?.home_expected?.toFixed(1)}</span></div>
                    <div className="flex justify-between items-center"><span className="text-slate-400">Visitante</span><span className="text-xl font-bold">{prediction.corners?.away_expected?.toFixed(1)}</span></div>
                    <div className="flex justify-between items-center border-t border-slate-800 pt-2"><span className="text-slate-300">Total</span><span className="text-xl font-bold text-green-400">{prediction.corners?.total_expected?.toFixed(1)}</span></div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader><CardTitle className="text-slate-100">Over/Under Córners</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {Object.entries(prediction.corners?.over_under || {}).map(([line, probs]: any) => (
                      <div key={line} className="flex justify-between items-center p-2 bg-slate-950 rounded">
                        <span className="text-slate-300">Más de {line}</span>
                        <span className="text-blue-400 font-bold">{(probs.over * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'Tarjetas' && (
              <div className="grid md:grid-cols-2 gap-6 animate-in fade-in duration-300">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader><CardTitle className="text-slate-100">Tarjetas Esperadas</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center"><span className="text-slate-400">Local</span><span className="text-xl font-bold">{prediction.cards?.home_expected?.toFixed(1)}</span></div>
                    <div className="flex justify-between items-center"><span className="text-slate-400">Visitante</span><span className="text-xl font-bold">{prediction.cards?.away_expected?.toFixed(1)}</span></div>
                    <div className="flex justify-between items-center border-t border-slate-800 pt-2"><span className="text-slate-300">Total</span><span className="text-xl font-bold text-yellow-500">{prediction.cards?.total_expected?.toFixed(1)}</span></div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader><CardTitle className="text-slate-100">Over/Under Tarjetas</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {Object.entries(prediction.cards?.over_under || {}).map(([line, probs]: any) => (
                      <div key={line} className="flex justify-between items-center p-2 bg-slate-950 rounded">
                        <span className="text-slate-300">Más de {line}</span>
                        <span className="text-blue-400 font-bold">{(probs.over * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'Remates' && (
              <div className="grid md:grid-cols-2 gap-6 animate-in fade-in duration-300">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader><CardTitle className="text-blue-400">Remates Local</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center"><span className="text-slate-400">Totales</span><span className="text-xl font-bold">{prediction.shots?.home_shots_expected?.toFixed(1)}</span></div>
                    <div className="flex justify-between items-center"><span className="text-slate-400">A Puerta</span><span className="text-xl font-bold text-green-400">{prediction.shots?.home_on_goal_expected?.toFixed(1)}</span></div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader><CardTitle className="text-red-400">Remates Visitante</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center"><span className="text-slate-400">Totales</span><span className="text-xl font-bold">{prediction.shots?.away_shots_expected?.toFixed(1)}</span></div>
                    <div className="flex justify-between items-center"><span className="text-slate-400">A Puerta</span><span className="text-xl font-bold text-green-400">{prediction.shots?.away_on_goal_expected?.toFixed(1)}</span></div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
