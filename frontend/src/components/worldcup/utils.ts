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
      isHomeNext: i % 2 !== 0,
      nextMatchId: `R16-${Math.ceil(i/2)}`
    };
  }
  
  // R16 (8 matches)
  for (let i = 1; i <= 8; i++) {
    bracket[`R16-${i}`] = {
      id: `R16-${i}`, round: 'R16', home_team: null, away_team: null,
      home_score: null, away_score: null, winner: null,
      isHomeNext: i % 2 !== 0,
      nextMatchId: `QF-${Math.ceil(i/2)}`
    };
  }
  
  // QF (4 matches)
  for (let i = 1; i <= 4; i++) {
    bracket[`QF-${i}`] = {
      id: `QF-${i}`, round: 'QF', home_team: null, away_team: null,
      home_score: null, away_score: null, winner: null,
      isHomeNext: i % 2 !== 0,
      nextMatchId: `SF-${Math.ceil(i/2)}`
    };
  }
  
  // SF (2 matches)
  for (let i = 1; i <= 2; i++) {
    bracket[`SF-${i}`] = {
      id: `SF-${i}`, round: 'SF', home_team: null, away_team: null,
      home_score: null, away_score: null, winner: null,
      isHomeNext: i % 2 !== 0,
      nextMatchId: `F-1`
    };
  }
  
  // Final (1 match)
  bracket['F-1'] = {
    id: `F-1`, round: 'F', home_team: null, away_team: null,
    home_score: null, away_score: null, winner: null,
    isHomeNext: true,
    nextMatchId: null
  };
  
  return bracket;
};
