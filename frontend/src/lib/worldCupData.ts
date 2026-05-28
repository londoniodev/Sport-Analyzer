export interface Team {
  name: string;
  flag: string;
  apiId: number; // API-Football national team ID
}

export interface Group {
  name: string;
  teams: Team[];
}

export const worldCupGroups: Group[] = [
  {
    name: 'Grupo A',
    teams: [
      { name: 'México', flag: '🇲🇽', apiId: 16 },
      { name: 'Sudáfrica', flag: '🇿🇦', apiId: 15 },
      { name: 'Corea del Sur', flag: '🇰🇷', apiId: 17 },
      { name: 'República Checa', flag: '🇨🇿', apiId: 773 }
    ]
  },
  {
    name: 'Grupo B',
    teams: [
      { name: 'Canadá', flag: '🇨🇦', apiId: 5529 },
      { name: 'Bosnia y Herzegovina', flag: '🇧🇦', apiId: 776 },
      { name: 'Qatar', flag: '🇶🇦', apiId: 1569 },
      { name: 'Suiza', flag: '🇨🇭', apiId: 14 }
    ]
  },
  {
    name: 'Grupo C',
    teams: [
      { name: 'Brasil', flag: '🇧🇷', apiId: 6 },
      { name: 'Marruecos', flag: '🇲🇦', apiId: 31 },
      { name: 'Haití', flag: '🇭🇹', apiId: 1577 },
      { name: 'Escocia', flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿', apiId: 1108 }
    ]
  },
  {
    name: 'Grupo D',
    teams: [
      { name: 'Estados Unidos', flag: '🇺🇸', apiId: 2384 },
      { name: 'Paraguay', flag: '🇵🇾', apiId: 2385 },
      { name: 'Australia', flag: '🇦🇺', apiId: 18 },
      { name: 'Turquía', flag: '🇹🇷', apiId: 777 }
    ]
  },
  {
    name: 'Grupo E',
    teams: [
      { name: 'Alemania', flag: '🇩🇪', apiId: 25 },
      { name: 'Curazao', flag: '🇨🇼', apiId: 145 },
      { name: 'Costa de Marfil', flag: '🇨🇮', apiId: 2381 },
      { name: 'Ecuador', flag: '🇪🇨', apiId: 2382 }
    ]
  },
  {
    name: 'Grupo F',
    teams: [
      { name: 'Países Bajos', flag: '🇳🇱', apiId: 1118 },
      { name: 'Japón', flag: '🇯🇵', apiId: 12 },
      { name: 'Suecia', flag: '🇸🇪', apiId: 1091 },
      { name: 'Túnez', flag: '🇹🇳', apiId: 28 }
    ]
  },
  {
    name: 'Grupo G',
    teams: [
      { name: 'Bélgica', flag: '🇧🇪', apiId: 1 },
      { name: 'Egipto', flag: '🇪🇬', apiId: 30 },
      { name: 'Irán', flag: '🇮🇷', apiId: 22 },
      { name: 'Nueva Zelanda', flag: '🇳🇿', apiId: 1530 }
    ]
  },
  {
    name: 'Grupo H',
    teams: [
      { name: 'España', flag: '🇪🇸', apiId: 9 },
      { name: 'Cabo Verde', flag: '🇨🇻', apiId: 1580 },
      { name: 'Arabia Saudita', flag: '🇸🇦', apiId: 23 },
      { name: 'Uruguay', flag: '🇺🇾', apiId: 7 }
    ]
  },
  {
    name: 'Grupo I',
    teams: [
      { name: 'Francia', flag: '🇫🇷', apiId: 2 },
      { name: 'Senegal', flag: '🇸🇳', apiId: 34 },
      { name: 'Irak', flag: '🇮🇶', apiId: 21 },
      { name: 'Noruega', flag: '🇳🇴', apiId: 1090 }
    ]
  },
  {
    name: 'Grupo J',
    teams: [
      { name: 'Argentina', flag: '🇦🇷', apiId: 26 },
      { name: 'Argelia', flag: '🇩🇿', apiId: 1559 },
      { name: 'Austria', flag: '🇦🇹', apiId: 775 },
      { name: 'Jordania', flag: '🇯🇴', apiId: 1571 }
    ]
  },
  {
    name: 'Grupo K',
    teams: [
      { name: 'Portugal', flag: '🇵🇹', apiId: 27 },
      { name: 'RD Congo', flag: '🇨🇩', apiId: 2379 },
      { name: 'Uzbekistán', flag: '🇺🇿', apiId: 1574 },
      { name: 'Colombia', flag: '🇨🇴', apiId: 1560 }
    ]
  },
  {
    name: 'Grupo L',
    teams: [
      { name: 'Inglaterra', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', apiId: 10 },
      { name: 'Croacia', flag: '🇭🇷', apiId: 3 },
      { name: 'Ghana', flag: '🇬🇭', apiId: 2383 },
      { name: 'Panamá', flag: '🇵🇦', apiId: 1563 }
    ]
  }
];

// Get all unique API IDs for bulk sync
export function getAllTeamApiIds(): number[] {
  return worldCupGroups.flatMap(g => g.teams.map(t => t.apiId));
}

// Get team info by API ID
export function getTeamByApiId(apiId: number): Team | undefined {
  for (const group of worldCupGroups) {
    const team = group.teams.find(t => t.apiId === apiId);
    if (team) return team;
  }
  return undefined;
}
