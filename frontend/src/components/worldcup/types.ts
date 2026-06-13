import type { Team } from '../../lib/worldCupData';

export interface SyncStatus {
  running: boolean;
  total: number;
  processed: number;
  current_team: string;
  errors: string[];
}

export interface WCFixture {
  id: number;
  date: string;
  home_team_id: number;
  away_team_id: number;
  home_team_name: string;
  away_team_name: string;
  home_score: number | null;
  away_score: number | null;
}

export interface Prediction {
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

export interface MonteCarloMatchResult {
  simulations: number;
  result_probs: { home: number; draw: number; away: number };
  score_distribution_top5: Record<string, number>;
}

export interface BracketMatch {
  id: string;
  round: 'R32' | 'R16' | 'QF' | 'SF' | 'F';
  home_team: Team | null;
  away_team: Team | null;
  home_score: number | null;
  away_score: number | null;
  winner: 'home' | 'away' | null;
  isHomeNext: boolean; 
  nextMatchId: string | null;
  
  // New Polla fields
  polla_score: { home: number; away: number } | null;
  is_draw_90: boolean;
  penalty_qualifier: 'home' | 'away' | null;
  montecarlo?: MonteCarloMatchResult;
}
