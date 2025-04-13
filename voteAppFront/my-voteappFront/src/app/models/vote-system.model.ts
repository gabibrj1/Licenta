export interface VoteSystem {
    id: string;
    name: string;
    description: string;
    category: string;
    created_at: Date;
    start_date: Date;
    end_date: Date;
    status: string;
    rules: any;
    options: VoteOption[];
    total_votes: number;
    require_email_verification: boolean;
    allowed_emails?: string;
  }
  
  export interface VoteOption {
    id: string;
    title: string;
    description?: string;
    image_url?: string;
    order: number;
    votes_count: number;
  }