export interface CatalogueShow {
  id: number;
  title: string;
  slug: string;
  synopsis: string;
  categories: string[];
  artwork: Record<string, string>;
  seasons: Record<string, CatalogueSeason>;
  trailers?: CatalogueTrailer[];
}

export interface CatalogueSeason {
  season_number: number;
  title: string;
  episodes: CatalogueEpisode[];
}

export interface CatalogueEpisode {
  content_group: string;
  title: string;
  episode_number: number;
  synopsis: string;
  duration_seconds: number;
  languages: string[];
  artwork: Record<string, string>;
}

export interface CatalogueTrailer {
  content_group: string;
  title: string;
  languages: string[];
  duration_seconds: number;
  artwork: Record<string, string>;
}

export interface CatalogueSection {
  name: string;
  shows: CatalogueShow[];
}

export interface Catalogue {
  version: number;
  generated_at: string;
  sections: Record<string, CatalogueSection>;
  meta: {
    total_shows: number;
    total_episodes: number;
  };
}
