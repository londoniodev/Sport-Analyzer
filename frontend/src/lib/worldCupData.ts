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
      { name: 'Sudáfrica', flag: '🇿🇦', apiId: 1531 },
      { name: 'Corea del Sur', flag: '🇰🇷', apiId: 17 },
      { name: 'República Checa', flag: '🇨🇿', apiId: 770 }
    ]
  },
  {
    name: 'Grupo B',
    teams: [
      { name: 'Canadá', flag: '🇨🇦', apiId: 5529 },
      { name: 'Bosnia y Herzegovina', flag: '🇧🇦', apiId: 1113 },
      { name: 'Qatar', flag: '🇶🇦', apiId: 1569 },
      { name: 'Suiza', flag: '🇨🇭', apiId: 15 }
    ]
  },
  {
    name: 'Grupo C',
    teams: [
      { name: 'Brasil', flag: '🇧🇷', apiId: 6 },
      { name: 'Marruecos', flag: '🇲🇦', apiId: 31 },
      { name: 'Haití', flag: '🇭🇹', apiId: 2386 },
      { name: 'Escocia', flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿', apiId: 1108 }
    ]
  },
  {
    name: 'Grupo D',
    teams: [
      { name: 'Estados Unidos', flag: '🇺🇸', apiId: 2384 },
      { name: 'Paraguay', flag: '🇵🇾', apiId: 2380 },
      { name: 'Australia', flag: '🇦🇺', apiId: 20 },
      { name: 'Turquía', flag: '🇹🇷', apiId: 777 }
    ]
  },
  {
    name: 'Grupo E',
    teams: [
      { name: 'Alemania', flag: '🇩🇪', apiId: 25 },
      { name: 'Curazao', flag: '🇨🇼', apiId: 5530 },
      { name: 'Costa de Marfil', flag: '🇨🇮', apiId: 1501 },
      { name: 'Ecuador', flag: '🇪🇨', apiId: 2382 }
    ]
  },
  {
    name: 'Grupo F',
    teams: [
      { name: 'Países Bajos', flag: '🇳🇱', apiId: 1118 },
      { name: 'Japón', flag: '🇯🇵', apiId: 12 },
      { name: 'Suecia', flag: '🇸🇪', apiId: 5 },
      { name: 'Túnez', flag: '🇹🇳', apiId: 28 }
    ]
  },
  {
    name: 'Grupo G',
    teams: [
      { name: 'Bélgica', flag: '🇧🇪', apiId: 1 },
      { name: 'Egipto', flag: '🇪🇬', apiId: 32 },
      { name: 'Irán', flag: '🇮🇷', apiId: 22 },
      { name: 'Nueva Zelanda', flag: '🇳🇿', apiId: 4673 }
    ]
  },
  {
    name: 'Grupo H',
    teams: [
      { name: 'España', flag: '🇪🇸', apiId: 9 },
      { name: 'Cabo Verde', flag: '🇨🇻', apiId: 1533 },
      { name: 'Arabia Saudita', flag: '🇸🇦', apiId: 23 },
      { name: 'Uruguay', flag: '🇺🇾', apiId: 7 }
    ]
  },
  {
    name: 'Grupo I',
    teams: [
      { name: 'Francia', flag: '🇫🇷', apiId: 2 },
      { name: 'Senegal', flag: '🇸🇳', apiId: 13 },
      { name: 'Irak', flag: '🇮🇶', apiId: 1567 },
      { name: 'Noruega', flag: '🇳🇴', apiId: 1090 }
    ]
  },
  {
    name: 'Grupo J',
    teams: [
      { name: 'Argentina', flag: '🇦🇷', apiId: 26 },
      { name: 'Argelia', flag: '🇩🇿', apiId: 1559 },
      { name: 'Austria', flag: '🇦🇹', apiId: 775 },
      { name: 'Jordania', flag: '🇯🇴', apiId: 1548 }
    ]
  },
  {
    name: 'Grupo K',
    teams: [
      { name: 'Portugal', flag: '🇵🇹', apiId: 27 },
      { name: 'RD Congo', flag: '🇨🇩', apiId: 1508 },
      { name: 'Uzbekistán', flag: '🇺🇿', apiId: 1568 },
      { name: 'Colombia', flag: '🇨🇴', apiId: 8 }
    ]
  },
  {
    name: 'Grupo L',
    teams: [
      { name: 'Inglaterra', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', apiId: 10 },
      { name: 'Croacia', flag: '🇭🇷', apiId: 3 },
      { name: 'Ghana', flag: '🇬🇭', apiId: 1504 },
      { name: 'Panamá', flag: '🇵🇦', apiId: 11 }
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
