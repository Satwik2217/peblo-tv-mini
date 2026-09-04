import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchCatalog } from '../api/client';
import type { Catalogue, CatalogueShow } from '../types';

function SearchResultCard({ show, onClick }: { show: CatalogueShow; onClick: (slug: string) => void }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  return (
    <div onClick={() => onClick(show.slug)} style={{ cursor: 'pointer', background: '#1a1a2e', borderRadius: '8px', padding: '16px', display: 'flex', gap: '16px', alignItems: 'center' }}>
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

export function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [language, setLanguage] = useState('');
  const [section, setSection] = useState('');
  const [searchTriggered, setSearchTriggered] = useState(false);

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
                <SearchResultCard key={show.id} show={show} onClick={(slug) => navigate(`/show/${slug}`)} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
