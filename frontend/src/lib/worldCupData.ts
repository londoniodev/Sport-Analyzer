export interface Team {
  name: string;
  flag: string;
}

export interface Group {
  name: string;
  teams: Team[];
}

export const worldCupGroups: Group[] = [
  {
    name: 'Grupo A',
    teams: [
      { name: 'México', flag: '🇲🇽' },
      { name: 'Sudáfrica', flag: '🇿🇦' },
      { name: 'Corea del Sur', flag: '🇰🇷' },
      { name: 'República Checa', flag: '🇨🇿' }
    ]
  },
  {
    name: 'Grupo B',
    teams: [
      { name: 'Canadá', flag: '🇨🇦' },
      { name: 'Bosnia y Herzegovina', flag: '🇧🇦' },
      { name: 'Qatar', flag: '🇶🇦' },
      { name: 'Suiza', flag: '🇨🇭' }
    ]
  },
  {
    name: 'Grupo C',
    teams: [
      { name: 'Brasil', flag: '🇧🇷' },
      { name: 'Marruecos', flag: '🇲🇦' },
      { name: 'Haití', flag: '🇭🇹' },
      { name: 'Escocia', flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿' }
    ]
  },
  {
    name: 'Grupo D',
    teams: [
      { name: 'Estados Unidos', flag: '🇺🇸' },
      { name: 'Paraguay', flag: '🇵🇾' },
      { name: 'Australia', flag: '🇦🇺' },
      { name: 'Turquía', flag: '🇹🇷' }
    ]
  },
  {
    name: 'Grupo E',
    teams: [
      { name: 'Alemania', flag: '🇩🇪' },
      { name: 'Curazao', flag: '🇨🇼' },
      { name: 'Costa de Marfil', flag: '🇨🇮' },
      { name: 'Ecuador', flag: '🇪🇨' }
    ]
  },
  {
    name: 'Grupo F',
    teams: [
      { name: 'Países Bajos', flag: '🇳🇱' },
      { name: 'Japón', flag: '🇯🇵' },
      { name: 'Suecia', flag: '🇸🇪' },
      { name: 'Túnez', flag: '🇹🇳' }
    ]
  },
  {
    name: 'Grupo G',
    teams: [
      { name: 'Bélgica', flag: '🇧🇪' },
      { name: 'Egipto', flag: '🇪🇬' },
      { name: 'Irán', flag: '🇮🇷' },
      { name: 'Nueva Zelanda', flag: '🇳🇿' }
    ]
  },
  {
    name: 'Grupo H',
    teams: [
      { name: 'España', flag: '🇪🇸' },
      { name: 'Cabo Verde', flag: '🇨🇻' },
      { name: 'Arabia Saudita', flag: '🇸🇦' },
      { name: 'Uruguay', flag: '🇺🇾' }
    ]
  },
  {
    name: 'Grupo I',
    teams: [
      { name: 'Francia', flag: '🇫🇷' },
      { name: 'Senegal', flag: '🇸🇳' },
      { name: 'Irak', flag: '🇮🇶' },
      { name: 'Noruega', flag: '🇳🇴' }
    ]
  },
  {
    name: 'Grupo J',
    teams: [
      { name: 'Argentina', flag: '🇦🇷' },
      { name: 'Argelia', flag: '🇩🇿' },
      { name: 'Austria', flag: '🇦🇹' },
      { name: 'Jordania', flag: '🇯🇴' }
    ]
  },
  {
    name: 'Grupo K',
    teams: [
      { name: 'Portugal', flag: '🇵🇹' },
      { name: 'RD Congo', flag: '🇨🇩' },
      { name: 'Uzbekistán', flag: '🇺🇿' },
      { name: 'Colombia', flag: '🇨🇴' }
    ]
  },
  {
    name: 'Grupo L',
    teams: [
      { name: 'Inglaterra', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
      { name: 'Croacia', flag: '🇭🇷' },
      { name: 'Ghana', flag: '🇬🇭' },
      { name: 'Panamá', flag: '🇵🇦' }
    ]
  }
];
