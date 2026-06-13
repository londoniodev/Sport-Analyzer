import { worldCupGroups } from '../../lib/worldCupData';
import type { BracketMatch } from './types';

// Get team flag or default
export const getFlag = (teamName: string) => {
  for (const group of worldCupGroups) {
    const team = group.teams.find(t => t.name === teamName);
    if (team) return team.flag;
  }
  return '🏳️';
};

// Pick a random score based on its probability
export const getWeightedRandomScore = (topScores: [string, any][]): string => {
  if (!topScores || topScores.length === 0) return '0-0';
  
  // Normalize probabilities in case they don't sum to 100%
  const totalProb = topScores.reduce((acc, curr) => acc + (curr[1] as number), 0);
  let rand = Math.random() * totalProb;
  let sum = 0;
  
  for (const [score, prob] of topScores) {
    sum += (prob as number);
    if (rand <= sum) return score;
  }
  
  return topScores[0][0] as string;
};

export const getOdds = (prob: number) => {
  if (!prob || prob <= 0) return '-';
  return (1 / prob).toFixed(2);
};

export const generateInitialBracket = (): Record<string, BracketMatch> => {
  const bracket: Record<string, BracketMatch> = {};
  
  // R32 (16 matches)
  for (let i = 1; i <= 16; i++) {
    bracket[`R32-${i}`] = {
      id: `R32-${i}`, round: 'R32', home_team: null, away_team: null,
      home_score: null, away_score: null, winner: null,
      polla_score: null, is_draw_90: false, penalty_qualifier: null,
      isHomeNext: i % 2 !== 0,
      nextMatchId: `R16-${Math.ceil(i/2)}`
    };
  }
  
  // R16 (8 matches)
  for (let i = 1; i <= 8; i++) {
    bracket[`R16-${i}`] = {
      id: `R16-${i}`, round: 'R16', home_team: null, away_team: null,
      home_score: null, away_score: null, winner: null,
      polla_score: null, is_draw_90: false, penalty_qualifier: null,
      isHomeNext: i % 2 !== 0,
      nextMatchId: `QF-${Math.ceil(i/2)}`
    };
  }
  
  // QF (4 matches)
  for (let i = 1; i <= 4; i++) {
    bracket[`QF-${i}`] = {
      id: `QF-${i}`, round: 'QF', home_team: null, away_team: null,
      home_score: null, away_score: null, winner: null,
      polla_score: null, is_draw_90: false, penalty_qualifier: null,
      isHomeNext: i % 2 !== 0,
      nextMatchId: `SF-${Math.ceil(i/2)}`
    };
  }
  
  // SF (2 matches)
  for (let i = 1; i <= 2; i++) {
    bracket[`SF-${i}`] = {
      id: `SF-${i}`, round: 'SF', home_team: null, away_team: null,
      home_score: null, away_score: null, winner: null,
      polla_score: null, is_draw_90: false, penalty_qualifier: null,
      isHomeNext: i % 2 !== 0,
      nextMatchId: `F-1`
    };
  }
  
  // Final (1 match)
  bracket['F-1'] = {
    id: `F-1`, round: 'F', home_team: null, away_team: null,
    home_score: null, away_score: null, winner: null,
    polla_score: null, is_draw_90: false, penalty_qualifier: null,
    isHomeNext: true,
    nextMatchId: null
  };
  
  return bracket;
};
