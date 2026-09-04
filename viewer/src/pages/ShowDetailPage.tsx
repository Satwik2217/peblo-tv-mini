import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCatalog } from '../api/client';
import type { Catalogue, CatalogueShow } from '../types';

function findShowBySlug(catalogue: Catalogue, slug: string): CatalogueShow | null {
  for (const section of Object.values(catalogue.sections)) {
    for (const show of section.shows) {
      if (show.slug === slug) return show;
    }
  }
  return null;
}

export function ShowDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [selectedLang, setSelectedLang] = useState<string>('en');

  const { data: catalogue, isLoading, error } = useQuery({
    queryKey: ['catalog'],
    queryFn: getCatalog,
  });

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: '#999', fontSize: '18px' }}>Loading...</p>
      </div>
    );
  }

  if (error || !catalogue) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
        <p style={{ color: '#999', fontSize: '18px' }}>No catalogue available yet.</p>
        <button onClick={() => navigate('/')} style={{ background: '#e50914', color: '#fff', border: 'none', padding: '8px 24px', borderRadius: '4px', cursor: 'pointer' }}>Go Home</button>
      </div>
    );
  }

  const cat = catalogue as Catalogue;
  const show = slug ? findShowBySlug(cat, slug) : null;

  if (!show) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
        <p style={{ color: '#999', fontSize: '18px' }}>Show not found.</p>
        <button onClick={() => navigate('/')} style={{ background: '#e50914', color: '#fff', border: 'none', padding: '8px 24px', borderRadius: '4px', cursor: 'pointer' }}>Go Home</button>
      </div>
    );
  }

  const seasons = Object.values(show.seasons || {});

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', paddingBottom: '48px' }}>
      {/* Nav */}
      <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, background: 'rgba(0,0,0,0.8)', padding: '16px clamp(24px, 5vw, 48px)' }}>
        <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', color: '#fff', fontSize: '16px', cursor: 'pointer' }}>&larr; Back</button>
      </nav>

      {/* Hero */}
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

      {/* Seasons */}
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
                                padding: '2px 8px', borderRadius: '4px', fontSize: '11px', border: 'none', cursor: 'pointer',
                                background: selectedLang === lang ? '#e50914' : 'rgba(255,255,255,0.1)', color: '#fff',
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

        {/* Trailers */}
        {show.trailers && show.trailers.length > 0 && (
          <div style={{ marginTop: '32px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: '#999' }}>Trailers</h2>
            <div style={{ display: 'flex', gap: '16px' }}>
              {show.trailers.map((trailer) => (
                <div key={trailer.content_group} style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', minWidth: '200px' }}>
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
