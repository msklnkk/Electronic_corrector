// src/types/user.types.ts

export interface UserProfile {
  user_id: number;
  email: string;
  username: string;
  first_name?: string;
  surname_name?: string;
  patronomic_name?: string;
  role: 'admin' | 'user';
  theme: 'light' | 'dark';
  is_push_enabled: boolean;
  tg_username?: string | null;
  telegram_id?: number | null;
  is_tg_subscribed?: boolean;
}

export interface UserStats {
  documents_count: number;
  average_compliance: number;
  average_time_minutes: number;
}

export interface Document {
  id: string;
  filename: string;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  score?: number;
}
