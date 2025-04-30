// Modele pentru cicluri electorale locale
export interface ElectionCycle {
    id: number;
    year: number;
    turnout_percentage: number | null;
    total_voters: number | null;
  }
  
  export interface ElectionCycleDetail extends ElectionCycle {
    description: string | null;
    candidates: SignificantCandidate[];
    events: ImportantEvent[];
  }
  
  // Modele pentru tipuri de alegeri locale
  export interface LocalElectionType {
    id: number;
    name: string;
    description: string;
  }
  
  // Modele pentru poziții administrative locale
  export interface LocalPosition {
    id: number;
    name: string;
    description: string;
    election_type: number;
    election_type_name?: string;
    importance: number;
    importance_display?: string;
  }
  
  // Modele pentru reguli electorale
  export interface LocalElectionRule {
    id: number;
    title: string;
    description: string;
    election_type: number;
    election_type_name?: string;
    since_year: number;
    is_current: boolean;
  }
  
  // Modele pentru candidați locali semnificativi
  export interface SignificantCandidate {
    id: number;
    name: string;
    slug: string;
    position: number;
    position_name?: string;
    location: string;
    election_cycle: number;
    election_year?: number;
    party: string;
    photo_url: string | null;
    achievement: string;
  }
  
  // Modele pentru evenimente importante
  export interface ImportantEvent {
    id: number;
    year: number;
    title: string;
    description: string;
    election_cycle: number | null;
    election_year?: number | null;
    importance: number;
    importance_display?: string;
  }
  
  // Modele pentru modificări legislative
  export interface LegislationChange {
    id: number;
    title: string;
    description: string;
    year: number;
    law_number: string | null;
    impact: string;
  }