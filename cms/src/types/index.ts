export interface User {
  id: number;
  email: string;
  username: string;
  role: 'editor' | 'admin';
  created_at: string;
}

export interface Show {
  id: number;
  title: string;
  slug: string;
  synopsis: string | null;
  section: string | null;
  categories: string[];
  status: string;
  created_at: string;
  updated_at: string;
  seasons_count: number;
  episodes_count: number;
}

export interface Season {
  id: number;
  show_id: number;
  season_number: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  episodes_count: number;
}

export interface ArtworkInfo {
  id: number;
  artwork_type: string;
  storage_key: string;
  width: number;
  height: number;
}

export interface Episode {
  id: number;
  season_id: number;
  title: string;
  synopsis: string | null;
  episode_number: number;
  duration_seconds: number | null;
  language: string;
  content_group: string;
  status: string;
  created_at: string;
  updated_at: string;
  artworks: ArtworkInfo[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PublishRun {
  id: number;
  initiated_by: number;
  started_at: string;
  completed_at: string | null;
  status: string;
  shows_count: number;
  episodes_count: number;
  catalogue_version: string | null;
  errors: string | null;
}

export interface ValidationReport {
  issues: {
    shows: Array<{ show_id: number; show_title: string; message: string }>;
    episodes: Array<{ episode_id: number; episode_title: string; show_title?: string; message: string }>;
    artwork: Array<{ episode_id?: number; episode_title?: string; show_title?: string; message: string }>;
    duplicates: Array<{ content_group: string; language: string; episode_ids: number[]; message: string }>;
  };
  total_blocking: number;
  summary: {
    shows_with_issues: number;
    episodes_with_issues: number;
    artwork_issues: number;
    duplicate_issues: number;
  };
}
