import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ArrowLeft, Activity, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from './ui/badge';

const TABS_CONFIG: Record<string, string[]> = {
  PARTIDO: ["tiempo_reglamentario", "medio_tiempo", "corners", "tarjetas_equipo", "disparos_equipo", "faltas_equipo", "eventos_partido"],
  JUGADORES: ["goleador", "tarjetas_jugador", "apuestas_especiales_jugador", "asistencias_jugador", "goles_jugador", "paradas_portero", "disparos_jugador"],
  HANDICAP: ["handicap_3way", "lineas_asiaticas"]
};

const CATEGORY_NAMES: Record<string, string> = {
  tiempo_reglamentario: "Tiempo Reglamentario",
  medio_tiempo: "Medio Tiempo",
  corners: "Tiros de Esquina",
  tarjetas_equipo: "Tarjetas por Equipo",
  disparos_equipo: "Disparos por Equipo",
  faltas_equipo: "Faltas por Equipo",
  eventos_partido: "Eventos del Partido",
  goleador: "Goleador del Partido",
  tarjetas_jugador: "Tarjetas (Jugador)",
  apuestas_especiales_jugador: "Especiales de Jugador",
  asistencias_jugador: "Asistencias",
  goles_jugador: "Goles del Jugador",
  paradas_portero: "Paradas del Portero",
  disparos_jugador: "Disparos (Jugador)",
  handicap_3way: "Hándicap 3-Way",
  lineas_asiaticas: "Líneas Asiáticas"
};

export default function RushbetDetailView({ eventId, onBack }: { eventId: string, onBack: () => void }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('PARTIDO');
  const [expandedCats, setExpandedCats] = useState<Record<string, boolean>>({
    tiempo_reglamentario: true
  });

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await fetch(`/api/rushbet/${eventId}`);
        if (res.ok) {
          const detail = await res.json();
          setData(detail);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [eventId]);

  const toggleCategory = (cat: string) => {
    setExpandedCats(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64 flex-col gap-4">
        <Activity className="w-10 h-10 animate-spin text-green-500" />
        <p className="text-slate-400">Descargando mercados desde Kambi...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl text-slate-300 mb-4">No se pudo cargar el evento</h2>
        <Button onClick={onBack} className="bg-slate-800">Volver a la lista</Button>
      </div>
    );
  }

  const renderMarketOutcomes = (outcomes: any[], marketLabel: string) => {
    const preds = data?.predictions;
    const labelLower = marketLabel.toLowerCase();
    
    // Detección del tipo de mercado
    const is1X2 = labelLower.includes('resultado final') || labelLower === '1x2';
    const isTotalGoals = labelLower.includes('total de goles') && !labelLower.includes('equipo');
    const isBTTS = labelLower.includes('ambos equipos marcarán') || labelLower.includes('ambos equipos anotan');
    const isCorners = (labelLower.includes('esquina') || labelLower.includes('corner')) && labelLower.includes('total');
    const isCards = labelLower.includes('tarjetas') && labelLower.includes('total');
    const isHandicap = labelLower.includes('hándicap') || labelLower.includes('handicap');

    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-3">
        {outcomes.map((out: any, idx: number) => {
          let prob: number | null = null;
          
          if (preds) {
            if (is1X2) {
               if (out.label === '1') prob = preds['1x2']?.home_win;
               if (out.label === 'X') prob = preds['1x2']?.draw;
               if (out.label === '2') prob = preds['1x2']?.away_win;
            } else if (isTotalGoals && out.line && preds.over_under?.[out.line]) {
               if (out.label === 'Over' || out.label === 'Más de') prob = preds.over_under[out.line]?.over;
               if (out.label === 'Under' || out.label === 'Menos de') prob = preds.over_under[out.line]?.under;
            } else if (isBTTS && preds.btts) {
               if (out.label === 'Sí' || out.label === 'Yes') prob = preds.btts?.yes;
               if (out.label === 'No') prob = preds.btts?.no;
            } else if (isCorners && out.line && preds.corners?.over_under?.[out.line]) {
               if (out.label === 'Over' || out.label === 'Más de') prob = preds.corners.over_under[out.line]?.over;
               if (out.label === 'Under' || out.label === 'Menos de') prob = preds.corners.over_under[out.line]?.under;
            } else if (isCards && out.line && preds.cards?.over_under?.[out.line]) {
               if (out.label === 'Over' || out.label === 'Más de') prob = preds.cards.over_under[out.line]?.over;
               if (out.label === 'Under' || out.label === 'Menos de') prob = preds.cards.over_under[out.line]?.under;
            } else if (isHandicap && out.line && preds.handicaps?.[out.line]) {
               if (out.label === '1') prob = preds.handicaps[out.line]?.win;
               if (out.label === '2') prob = preds.handicaps[out.line]?.loss;
               if (out.label === 'X' || out.label === 'Empate') prob = preds.handicaps[out.line]?.push;
            }
          }
          
          return (
            <div key={idx} className="bg-[#121214] border border-slate-800 rounded p-3 flex justify-between items-center hover:border-green-500/50 transition-colors">
              <div className="flex flex-col">
                <span className="text-sm text-slate-300 font-medium truncate pr-2">
                  {out.label} {out.line ? <span className="text-slate-500">({out.line})</span> : ''}
                </span>
                {prob !== null && (
                  <span className="text-xs text-blue-400 font-bold tracking-wide mt-1">
                    🤖 {(prob * 100).toFixed(1)}%
                  </span>
                )}
              </div>
              <span className="text-green-400 font-mono font-bold text-lg">{out.odds.toFixed(2)}</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-right-8 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4 border-b border-slate-800 pb-4">
        <Button onClick={onBack} variant="outline" className="border-slate-700 bg-slate-900">
          <ArrowLeft className="w-4 h-4 mr-2" /> Volver
        </Button>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            {data.home_team} vs {data.away_team}
            {data.predictions && <Badge className="bg-blue-600 ml-2">🤖 AI Powered</Badge>}
          </h2>
          <p className="text-slate-400 text-sm mt-1">{data.name}</p>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex gap-2 border-b border-slate-800">
        {['PARTIDO', 'JUGADORES', 'HANDICAP'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 font-semibold text-sm transition-colors border-b-2 ${
              activeTab === tab 
                ? 'border-green-500 text-green-400 bg-green-500/10' 
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Markets Content */}
      <div className="space-y-4 pb-12">
        {TABS_CONFIG[activeTab].map(category => {
          const catMarkets = data.markets[category] || [];
          if (catMarkets.length === 0) return null;
          
          const isExpanded = expandedCats[category] ?? false; // Fixed issue where some weren't expanded explicitly
          
          return (
            <Card key={category} className="bg-slate-900 border-slate-800 overflow-hidden">
              <div 
                className="flex justify-between items-center p-4 cursor-pointer hover:bg-slate-800/50 transition-colors"
                onClick={() => toggleCategory(category)}
              >
                <div className="flex items-center gap-3">
                  <h3 className="font-bold text-slate-200">{CATEGORY_NAMES[category] || category}</h3>
                  <Badge variant="outline" className="bg-slate-950 border-slate-700">{catMarkets.length}</Badge>
                </div>
                {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500" />}
              </div>
              
              {isExpanded && (
                <div className="border-t border-slate-800 p-4 space-y-6">
                  {catMarkets.map((market: any, i: number) => (
                    <div key={i} className="bg-slate-950/50 rounded-lg p-4 border border-slate-800/50">
                      <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-3">
                        {market.label}
                      </h4>
                      {renderMarketOutcomes(market.outcomes, market.label)}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
