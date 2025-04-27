export interface PresidentialCandidate {
    id: number;
    name: string;
    slug: string;
    birth_date: string | null;
    party: string;
    photo_url: string | null;
    biography: string;
    political_experience: string | null;
    education: string | null;
    is_current: boolean;
    participations?: ElectionParticipation[]; // Adăugat ca opțional
  }
  
  export interface CandidateDetail extends PresidentialCandidate {
    participations: ElectionParticipation[];
    controversies: Controversy[];
  }
  
  export interface ElectionParticipation {
    id: number;
    candidate: number;
    candidate_name: string;
    candidate_party: string;
    election_year: number;
    year: number;
    votes_count: number | null;
    votes_percentage: number | null;
    position: number | null;
    round: number;
    round_display: string;
    campaign_slogan: string | null;
    notable_events: string | null;
  }
  
  export interface Controversy {
    id: number;
    title: string;
    description: string;
    date: string;
    candidate: number | null;
    candidate_name: string | null;
    election_year: number | null;
    election_year_value: number | null;
    impact: string | null;
  }
  
  export interface ElectionYear {
    id: number;
    year: number;
    description: string | null;
    turnout_percentage: number | null;
    total_voters: number | null;
  }
  
  export interface ElectionYearDetail extends ElectionYear {
    participations: ElectionParticipation[];
    media_influences: MediaInfluence[];
    controversies: Controversy[];
  }
  
  export interface MediaInfluence {
    id: number;
    title: string;
    description: string;
    election_year: number;
    media_type: string;
    media_type_display: string;
    impact_level: number;
    impact_level_display: string;
  }
  
  export interface HistoricalEvent {
    id: number;
    year: number;
    title: string;
    description: string;
    importance: number;
  }