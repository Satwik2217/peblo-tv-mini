import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCatalog } from '../api/client';
import type { Catalogue, CatalogueShow, CatalogueSection } from '../types';

function HeroBanner({ show, onClick }: { show: CatalogueShow; onClick: (slug: string) => void }) {
  const bannerUrl = show.artwork?.banner;
  return (
    <div onClick={() => onClick(show.slug)} style={{ position: 'relative', width: '100%', height: 'clamp(400px, 60vw, 500px)', overflow: 'hidden', background: '#1a1a2e', cursor: 'pointer' }}>
      {bannerUrl && (
        <img src={bannerUrl} alt={show.title} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
      )}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'linear-gradient(transparent, rgba(0,0,0,0.9))', padding: 'clamp(40px, 6vw, 60px) clamp(24px, 5vw, 48px) 40px' }}>
        <h1 style={{ fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 700, marginBottom: '8px', lineHeight: 1.2 }}>{show.title}</h1>
        <p style={{ fontSize: 'clamp(14px, 2vw, 16px)', color: '#ccc', maxWidth: '600px', marginBottom: '12px', lineHeight: 1.5 }}>{show.synopsis}</p>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {show.categories?.map((cat: string) => (
            <span key={cat} style={{ padding: '4px 12px', background: 'rgba(255,255,255,0.15)', borderRadius: '16px', fontSize: '12px' }}>{cat}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function ShowCard({ show, onClick }: { show: CatalogueShow; onClick: (slug: string) => void }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  return (
    <div onClick={() => onClick(show.slug)} style={{ cursor: 'pointer', minWidth: '180px', width: '180px', flexShrink: 0 }}>
      <div style={{ width: '180px', height: '270px', borderRadius: '8px', overflow: 'hidden', background: '#1a1a2e', position: 'relative' }}>
        {!imgLoaded && !imgError && <div style={{ position: 'absolute', inset: 0, background: '#2a2a3e', animation: 'pulse 1.5s infinite' }} />}
        {!imgError && show.artwork?.poster ? (
          <img
            src={show.artwork.poster}
            alt={show.title}
            loading="lazy"
            onLoad={() => setImgLoaded(true)}
            onError={() => setImgError(true)}
            style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: imgLoaded ? 1 : 0, transition: 'opacity 0.3s' }}
          />
        ) : (
          <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', fontSize: '14px' }}>No Image</div>
        )}
      </div>
      <p style={{ marginTop: '8px', fontSize: '14px', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{show.title}</p>
    </div>
  );
}

function SectionRow({ section, onShowClick }: { section: CatalogueSection; onShowClick: (slug: string) => void }) {
  return (
    <div style={{ marginBottom: '32px' }}>
      <h2 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '16px', paddingLeft: 'clamp(24px, 5vw, 48px)', flex: 'none' }}>{section.name.charAt(0).toUpperCase() + section.name.slice(1)}</h2>
      <div style={{ display: 'flex', gap: '16px', paddingLeft: 'clamp(24px, 5vw, 48px)', paddingRight: 'clamp(24px, 5vw, 48px)', overflowX: 'auto', paddingBottom: '8px', scrollbarWidth: 'thin', scrollbarColor: '#555 transparent', WebkitOverflowScrolling: 'touch' }}>
        {section.shows.map((show) => (
          <ShowCard key={show.id} show={show} onClick={onShowClick} />
        ))}
      </div>
    </div>
  );
}

export function HomePage() {
  const navigate = useNavigate();
  const { data: catalogue, isLoading, error } = useQuery({
    queryKey: ['catalog'],
    queryFn: getCatalog,
  });

  const cat = catalogue as Catalogue | undefined;
  const sections = cat ? Object.values(cat.sections) : [];
  const heroShow = sections.length > 0 && sections[0].shows.length > 0 ? sections[0].shows[0] : null;

  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleShowClick = (slug: string) => navigate(`/show/${slug}`);

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: '#999', fontSize: '18px' }}>Loading Peblo TV...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
        <p style={{ color: '#999', fontSize: '18px' }}>No catalogue available yet.</p>
        <p style={{ color: '#666', fontSize: '14px' }}>Ask an admin to publish the catalogue first.</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a' }}>
      {/* Nav */}
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        background: scrolled ? 'rgba(10,10,10,0.95)' : 'linear-gradient(rgba(0,0,0,0.8), transparent)',
        transition: 'background 0.3s ease',
        padding: '16px clamp(24px, 5vw, 48px)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#e50914' }}>Peblo TV</h1>
        <div style={{ display: 'flex', gap: '16px' }}>
          <a href="/search" style={{ color: '#fff', textDecoration: 'none', fontSize: '14px' }}>Search</a>
        </div>
      </nav>

      {/* Hero */}
      {heroShow && <HeroBanner show={heroShow} onClick={handleShowClick} />}

      {/* Sections */}
      <div style={{ paddingTop: '24px', paddingBottom: '48px' }}>
        {sections.map((section) => (
          section.shows.length > 0 && (
            <SectionRow key={section.name} section={section} onShowClick={handleShowClick} />
          )
        ))}
      </div>
    </div>
  );
}
