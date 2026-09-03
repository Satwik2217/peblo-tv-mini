import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchCatalog } from '../api/client';
import type { Catalogue, CatalogueShow } from '../types';

function SearchResultCard({ show, onClick }: { show: CatalogueShow; onClick: () => void }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  return (
    <div onClick={onClick} style={{ cursor: 'pointer', background: '#1a1a2e', borderRadius: '8px', padding: '16px', display: 'flex', gap: '16px', alignItems: 'center' }}>
      <div style={{ width: '100px', height: '150px', borderRadius: '4px', overflow: 'hidden', background: '#2a2a3e', flexShrink: 0 }}>
        {show.artwork?.poster ? (
          <img src={show.artwork.poster} alt={show.title} loading="lazy" onLoad={() => setImgLoaded(true)} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: imgLoaded ? 1 : 0, transition: 'opacity 0.3s' }} />
        ) : (
          <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', fontSize: '12px' }}>No Image</div>
        )}
      </div>
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '4px' }}>{show.title}</h3>
        <p style={{ fontSize: '13px', color: '#999', marginBottom: '8px' }}>{show.synopsis}</p>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {show.categories?.map((cat: string) => (
            <span key={cat} style={{ padding: '2px 8px', background: 'rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '11px' }}>{cat}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function SearchShowDetail({ show, onBack }: { show: CatalogueShow; onBack: () => void }) {
  const seasons = Object.values(show.seasons || {});
  const [selectedLang, setSelectedLang] = useState<string>('en');

  return (
    <div style={{ minHeight: '100vh', paddingBottom: '48px' }}>
      <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, background: 'rgba(0,0,0,0.8)', padding: '16px clamp(24px, 5vw, 48px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxSizing: 'border-box' }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: '#fff', fontSize: '16px', cursor: 'pointer' }}>&larr; Back to Search</button>
        <a href="/" style={{ color: '#e50914', textDecoration: 'none', fontSize: '20px', fontWeight: 700, whiteSpace: 'nowrap' }}>Peblo TV</a>
      </nav>

      <div style={{ position: 'relative', width: '100%', minHeight: 'min(80vw, 460px)', paddingTop: '64px', overflow: 'hidden', background: '#1a1a2e', display: 'flex', alignItems: 'flex-end' }}>
        {show.artwork?.banner && (
          <img src={show.artwork.banner} alt={show.title} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
        )}
        <div style={{ position: 'relative', width: '100%', background: 'linear-gradient(transparent, rgba(0,0,0,0.9))', padding: 'clamp(40px, 6vw, 60px) clamp(24px, 5vw, 48px) 32px' }}>
          <h1 style={{ fontSize: 'clamp(28px, 5vw, 36px)', fontWeight: 700, marginBottom: '8px', lineHeight: 1.2 }}>{show.title}</h1>
          <p style={{ fontSize: 'clamp(13px, 2vw, 15px)', color: '#ccc', maxWidth: '600px', marginBottom: '12px', lineHeight: 1.5 }}>{show.synopsis}</p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {show.categories?.map((cat: string) => (
              <span key={cat} style={{ padding: '4px 12px', background: 'rgba(255,255,255,0.15)', borderRadius: '16px', fontSize: '12px' }}>{cat}</span>
            ))}
          </div>
        </div>
      </div>

      <div style={{ padding: '32px clamp(24px, 5vw, 48px)' }}>
        {seasons.map((season) => (
          <div key={season.season_number} style={{ marginBottom: '32px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px' }}>{season.title}</h2>
            <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))' }}>
              {season.episodes.map((ep) => (
                <div key={ep.content_group} style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                  {ep.artwork?.thumbnail && (
                    <img src={ep.artwork.thumbnail} alt={ep.title} loading="lazy" style={{ width: '160px', height: '90px', objectFit: 'cover', borderRadius: '4px', flexShrink: 0 }} />
                  )}
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 500, marginBottom: '4px' }}>{ep.episode_number}. {ep.title}</h3>
                    {ep.synopsis && <p style={{ fontSize: '13px', color: '#999', marginBottom: '8px' }}>{ep.synopsis}</p>}
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '12px', color: '#999' }}>{Math.floor(ep.duration_seconds / 60)}m {ep.duration_seconds % 60}s</span>
                      {ep.languages.length > 1 && (
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {ep.languages.map((lang) => (
                            <button
                              key={lang}
                              onClick={() => setSelectedLang(lang)}
                              style={{
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontSize: '11px',
                                border: 'none',
                                cursor: 'pointer',
                                background: selectedLang === lang ? '#e50914' : 'rgba(255,255,255,0.1)',
                                color: '#fff',
                              }}
                            >
                              {lang === 'en' ? 'English' : lang === 'hi' ? 'Hindi' : lang}
                            </button>
                          ))}
                        </div>
                      )}
                      {ep.languages.length === 1 && (
                        <span style={{ fontSize: '11px', color: '#999' }}>{ep.languages[0] === 'en' ? 'English' : ep.languages[0] === 'hi' ? 'Hindi' : ep.languages[0]}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {show.trailers && show.trailers.length > 0 && (
          <div style={{ marginTop: '32px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#999' }}>Trailers</h2>
            <div style={{ display: 'flex', gap: '16px', overflowX: 'auto', paddingBottom: '8px' }}>
              {show.trailers.map((trailer) => (
                <div key={trailer.content_group} style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', minWidth: '200px', flexShrink: 0 }}>
                  <h3 style={{ fontSize: '14px', marginBottom: '4px' }}>{trailer.title}</h3>
                  <p style={{ fontSize: '12px', color: '#999' }}>{trailer.duration_seconds}s</p>
                  <p style={{ fontSize: '11px', color: '#666' }}>Languages: {trailer.languages.join(', ')}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [language, setLanguage] = useState('');
  const [section, setSection] = useState('');
  const [searchTriggered, setSearchTriggered] = useState(false);
  const [selectedShow, setSelectedShow] = useState<CatalogueShow | null>(null);

  const params: Record<string, string> = {};
  if (query) params.q = query;
  if (category) params.category = category;
  if (language) params.language = language;
  if (section) params.section = section;

  const { data: results, isLoading } = useQuery({
    queryKey: ['catalogSearch', params],
    queryFn: () => searchCatalog(params),
    enabled: searchTriggered,
  });

  const cat = results as Catalogue | undefined;
  const sections = cat ? Object.values(cat.sections) : [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchTriggered(true);
  };

  if (selectedShow) {
    return <SearchShowDetail show={selectedShow} onBack={() => setSelectedShow(null)} />;
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a' }}>
      <nav style={{ padding: '16px clamp(24px, 5vw, 48px)', background: '#111', borderBottom: '1px solid #333', display: 'flex', alignItems: 'center' }}>
        <a href="/" style={{ color: '#e50914', textDecoration: 'none', fontSize: '20px', fontWeight: 700, whiteSpace: 'nowrap' }}>Peblo TV</a>
      </nav>

      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '32px clamp(24px, 5vw, 48px)' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '24px' }}>Search</h1>

        <form onSubmit={handleSearch} style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '12px', flexWrap: 'wrap' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search shows, episodes, categories..."
              style={{ flex: 1, minWidth: '200px', padding: '12px', background: '#1a1a2e', border: '1px solid #333', borderRadius: '4px', color: '#fff', fontSize: '16px' }}
            />
            <button type="submit" style={{ padding: '12px 24px', background: '#e50914', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px', whiteSpace: 'nowrap' }}>Search</button>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <select value={category} onChange={(e) => { setCategory(e.target.value); setSearchTriggered(true); }} style={{ flex: '1', minWidth: '140px', padding: '8px', background: '#1a1a2e', border: '1px solid #333', borderRadius: '4px', color: '#fff' }}>
              <option value="">All Categories</option>
              {['adventure', 'folk', 'friendship', 'india', 'language', 'learning', 'maths', 'music', 'nature', 'reading', 'science', 'singalong', 'stories', 'travel', 'values'].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <select value={language} onChange={(e) => { setLanguage(e.target.value); setSearchTriggered(true); }} style={{ flex: '1', minWidth: '140px', padding: '8px', background: '#1a1a2e', border: '1px solid #333', borderRadius: '4px', color: '#fff' }}>
              <option value="">All Languages</option>
              <option value="en">English</option>
              <option value="hi">Hindi</option>
            </select>
            <select value={section} onChange={(e) => { setSection(e.target.value); setSearchTriggered(true); }} style={{ flex: '1', minWidth: '140px', padding: '8px', background: '#1a1a2e', border: '1px solid #333', borderRadius: '4px', color: '#fff' }}>
              <option value="">All Sections</option>
              {['featured', 'series', 'minisodes', 'songs'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </form>

        {isLoading && <p style={{ color: '#999' }}>Searching...</p>}

        {searchTriggered && !isLoading && sections.length === 0 && (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <p style={{ fontSize: '18px', color: '#666', marginBottom: '8px' }}>No shows found.</p>
            <p style={{ fontSize: '14px', color: '#555' }}>Try a different search or remove one of the filters.</p>
          </div>
        )}

        {sections.map((sectionData) => (
          <div key={sectionData.name} style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px', color: '#999' }}>{sectionData.name}</h2>
            <div style={{ display: 'grid', gap: '12px' }}>
              {sectionData.shows.map((show) => (
                <SearchResultCard key={show.id} show={show} onClick={() => setSelectedShow(show)} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
