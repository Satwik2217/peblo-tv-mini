import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getShows, getEpisodes, getSeasons, createShow, updateShow, deleteShow, createSeason, createEpisode, updateEpisode, deleteEpisode, getValidationReport, publishCatalog, getPublishRuns, uploadArtwork } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import type { Show, Episode, Season, ValidationReport, PublishRun, PaginatedResponse } from '../types';

const VALID_SECTIONS = ['featured', 'series', 'minisodes', 'songs'];
const VALID_CATEGORIES = ['adventure', 'folk', 'friendship', 'india', 'language', 'learning', 'maths', 'music', 'nature', 'reading', 'science', 'singalong', 'stories', 'travel', 'values'];

function ArtworkUpload({ episodeId, showId, onUploaded }: { episodeId?: number; showId?: number; onUploaded?: () => void }) {
  const [uploading, setUploading] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [previews, setPreviews] = useState<Record<string, string>>({});

  const specs = {
    poster: { label: 'Poster', desc: '2:3 ratio, ~600x900px, max 200 KB' },
    banner: { label: 'Banner', desc: '16:9 ratio, ~1280x720px, max 200 KB' },
    thumbnail: { label: 'Thumbnail', desc: '16:9 ratio, ~640x360px, max 200 KB' },
  };

  const handleUpload = async (type: string, file: File) => {
    setUploading(type);
    setErrors((prev) => ({ ...prev, [type]: '' }));

    // Client-side pre-validation
    if (file.size > 200 * 1024) {
      setErrors((prev) => ({ ...prev, [type]: `File is ${(file.size / 1024).toFixed(0)} KB. Maximum is 200 KB.` }));
      setUploading(null);
      return;
    }

    const formData = new FormData();
    formData.append('artwork_type', type);
    formData.append('file', file);
    if (episodeId) formData.append('episode_id', String(episodeId));
    if (showId) formData.append('show_id', String(showId));

    try {
      await uploadArtwork(formData);
      setPreviews((prev) => ({ ...prev, [type]: URL.createObjectURL(file) }));
      onUploaded?.();
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, [type]: err.message }));
    } finally {
      setUploading(null);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
      {(Object.entries(specs) as [string, { label: string; desc: string }][]).map(([type, spec]) => (
        <div key={type} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
          <h4 style={{ marginBottom: '4px' }}>{spec.label}</h4>
          <p style={{ fontSize: '12px', color: '#666', marginBottom: '12px' }}>{spec.desc}</p>
          {previews[type] && (
            <img src={previews[type]} alt={spec.label} style={{ width: '100%', height: '120px', objectFit: 'cover', borderRadius: '4px', marginBottom: '8px' }} />
          )}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(type, file);
            }}
            style={{ fontSize: '12px' }}
          />
          {uploading === type && <p style={{ color: '#4f46e5', fontSize: '12px', marginTop: '4px' }}>Uploading...</p>}
          {errors[type] && <p style={{ color: '#c00', fontSize: '12px', marginTop: '4px', whiteSpace: 'pre-wrap' }}>{errors[type]}</p>}
        </div>
      ))}
    </div>
  );
}

function ShowForm({ show, onSave, onCancel }: { show?: Show; onSave: (data: any) => void; onCancel: () => void }) {
  const [title, setTitle] = useState(show?.title || '');
  const [synopsis, setSynopsis] = useState(show?.synopsis || '');
  const [section, setSection] = useState(show?.section || '');
  const [categories, setCategories] = useState<string[]>(show?.categories || []);
  const [status, setStatus] = useState(show?.status || 'draft');

  return (
    <div style={{ background: 'white', padding: '24px', borderRadius: '8px', marginBottom: '16px' }}>
      <h3 style={{ marginBottom: '16px' }}>{show ? 'Edit Show' : 'Create Show'}</h3>
      <div style={{ display: 'grid', gap: '12px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }} />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Synopsis</label>
          <textarea value={synopsis} onChange={(e) => setSynopsis(e.target.value)} rows={3} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }} />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Section</label>
          <select value={section} onChange={(e) => setSection(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
            <option value="">None</option>
            {VALID_SECTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Categories</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {VALID_CATEGORIES.map((cat) => (
              <label key={cat} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px' }}>
                <input
                  type="checkbox"
                  checked={categories.includes(cat)}
                  onChange={(e) => {
                    if (e.target.checked) setCategories([...categories, cat]);
                    else setCategories(categories.filter((c) => c !== cat));
                  }}
                />
                {cat}
              </label>
            ))}
          </div>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => onSave({ title, synopsis, section: section || null, categories, status })} style={{ padding: '8px 16px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            {show ? 'Update' : 'Create'}
          </button>
          <button onClick={onCancel} style={{ padding: '8px 16px', background: '#e5e7eb', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

function EpisodeForm({ episode, showId, onSave, onCancel }: { episode?: Episode; showId?: number; onSave: (data: any) => void; onCancel: () => void }) {
  const [title, setTitle] = useState(episode?.title || '');
  const [synopsis, setSynopsis] = useState(episode?.synopsis || '');
  const [episodeNumber, setEpisodeNumber] = useState(episode?.episode_number || 1);
  const [duration, setDuration] = useState(episode?.duration_seconds || 0);
  const [language, setLanguage] = useState(episode?.language || 'en');
  const [contentGroup, setContentGroup] = useState(episode?.content_group || '');
  const [status, setStatus] = useState(episode?.status || 'draft');
  const [seasonId, setSeasonId] = useState(episode?.season_id || 0);

  const { data: seasonsData } = useQuery({
    queryKey: ['seasons', showId],
    queryFn: () => getSeasons(showId ? { show_id: String(showId) } : {}),
    enabled: !!showId,
  });

  const seasons = seasonsData?.items || [];

  return (
    <div style={{ background: 'white', padding: '24px', borderRadius: '8px', marginBottom: '16px' }}>
      <h3 style={{ marginBottom: '16px' }}>{episode ? 'Edit Episode' : 'Create Episode'}</h3>
      <div style={{ display: 'grid', gap: '12px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Season</label>
          <select value={seasonId} onChange={(e) => setSeasonId(Number(e.target.value))} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
            <option value={0}>Select season</option>
            {seasons.map((s: Season) => <option key={s.id} value={s.id}>Season {s.season_number} - {s.title || `Season ${s.season_number}`}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }} />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Synopsis</label>
          <textarea value={synopsis || ''} onChange={(e) => setSynopsis(e.target.value)} rows={2} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Episode #</label>
            <input type="number" value={episodeNumber} onChange={(e) => setEpisodeNumber(Number(e.target.value))} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Duration (sec)</label>
            <input type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value))} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Language</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
              <option value="en">English</option>
              <option value="hi">Hindi</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}>Content Group</label>
          <input value={contentGroup} onChange={(e) => setContentGroup(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }} />
          <p style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>Episodes sharing the same content_group are language variants of the same episode.</p>
        </div>
        {episode && (
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Artwork</label>
            <ArtworkUpload episodeId={episode.id} />
          </div>
        )}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => onSave({ season_id: seasonId, title, synopsis, episode_number: episodeNumber, duration_seconds: duration || null, language, content_group: contentGroup, status })} style={{ padding: '8px 16px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            {episode ? 'Update' : 'Create'}
          </button>
          <button onClick={onCancel} style={{ padding: '8px 16px', background: '#e5e7eb', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'shows' | 'episodes' | 'publish'>('shows');
  const [search, setSearch] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [languageFilter, setLanguageFilter] = useState('');
  const [page, setPage] = useState(1);
  const [editingShow, setEditingShow] = useState<Show | null>(null);
  const [showingCreateShow, setShowingCreateShow] = useState(false);
  const [editingEpisode, setEditingEpisode] = useState<Episode | null>(null);
  const [showingCreateEpisode, setShowingCreateEpisode] = useState(false);
  const [selectedShowId, setSelectedShowId] = useState<number | null>(null);

  // Shows
  const showsParams: Record<string, string> = { page: String(page), page_size: '10' };
  if (search) showsParams.search = search;
  if (sectionFilter) showsParams.section = sectionFilter;
  if (statusFilter) showsParams.status_filter = statusFilter;

  const { data: showsData, isLoading: showsLoading } = useQuery({
    queryKey: ['shows', showsParams],
    queryFn: () => getShows(showsParams),
    enabled: tab === 'shows',
  });

  // Episodes
  const epsParams: Record<string, string> = { page: String(page), page_size: '15' };
  if (search) epsParams.search = search;
  if (languageFilter) epsParams.language = languageFilter;
  if (statusFilter) epsParams.status_filter = statusFilter;
  if (selectedShowId) epsParams.show_id = String(selectedShowId);

  const { data: episodesData, isLoading: episodesLoading } = useQuery({
    queryKey: ['episodes', epsParams],
    queryFn: () => getEpisodes(epsParams),
    enabled: tab === 'episodes',
  });

  // Validation
  const { data: validationData } = useQuery({
    queryKey: ['validation'],
    queryFn: getValidationReport,
    enabled: tab === 'publish',
  });

  // Publish runs
  const { data: runsData } = useQuery({
    queryKey: ['publishRuns'],
    queryFn: getPublishRuns,
    enabled: tab === 'publish',
  });

  // Mutations
  const createShowMutation = useMutation({
    mutationFn: createShow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shows'] });
      setShowingCreateShow(false);
    },
  });

  const updateShowMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateShow(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shows'] });
      setEditingShow(null);
    },
  });

  const deleteShowMutation = useMutation({
    mutationFn: deleteShow,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['shows'] }),
  });

  const createEpisodeMutation = useMutation({
    mutationFn: createEpisode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['episodes'] });
      setShowingCreateEpisode(false);
    },
  });

  const updateEpisodeMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => updateEpisode(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['episodes'] });
      setEditingEpisode(null);
    },
  });

  const deleteEpisodeMutation = useMutation({
    mutationFn: deleteEpisode,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['episodes'] }),
  });

  const publishMutation = useMutation({
    mutationFn: publishCatalog,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publishRuns'] });
      queryClient.invalidateQueries({ queryKey: ['validation'] });
    },
  });

  const validation = validationData as ValidationReport | undefined;
  const runs = runsData?.items || [];

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      {/* Header */}
      <header style={{ background: 'white', borderBottom: '1px solid #e5e7eb', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h1 style={{ fontSize: '18px', fontWeight: 700 }}>Peblo TV CMS</h1>
          <nav style={{ display: 'flex', gap: '4px' }}>
            {(['shows', 'episodes', 'publish'] as const).map((t) => (
              <button key={t} onClick={() => { setTab(t); setPage(1); }}
                style={{ padding: '6px 12px', border: 'none', borderRadius: '4px', cursor: 'pointer', background: tab === t ? '#4f46e5' : 'transparent', color: tab === t ? 'white' : '#666', fontWeight: tab === t ? 600 : 400 }}>
                {t === 'publish' ? 'Publish' : t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '13px', color: '#666' }}>{user?.email} ({user?.role})</span>
          <button onClick={logout} style={{ padding: '6px 12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}>Logout</button>
        </div>
      </header>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
        {/* Shows Tab */}
        {tab === 'shows' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2>Shows</h2>
              <button onClick={() => setShowingCreateShow(true)} style={{ padding: '8px 16px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>+ New Show</button>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
              <input placeholder="Search shows..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px', width: '200px' }} />
              <select value={sectionFilter} onChange={(e) => { setSectionFilter(e.target.value); setPage(1); }} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
                <option value="">All Sections</option>
                {VALID_SECTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
                <option value="">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="published">Published</option>
              </select>
            </div>

            {showingCreateShow && <ShowForm onSave={(data) => createShowMutation.mutate(data)} onCancel={() => setShowingCreateShow(false)} />}
            {editingShow && <ShowForm show={editingShow} onSave={(data) => updateShowMutation.mutate({ id: editingShow.id, data })} onCancel={() => setEditingShow(null)} />}

            {showsLoading ? <p>Loading...</p> : (
              <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden' }}>
                {(showsData?.items || []).map((show: Show) => (
                  <div key={show.id} style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{show.title}</strong>
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#999' }}>{show.slug}</span>
                      <span style={{ marginLeft: '8px', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', background: show.status === 'published' ? '#dcfce7' : '#f3f4f6', color: show.status === 'published' ? '#166534' : '#666' }}>{show.status}</span>
                      {show.section && <span style={{ marginLeft: '8px', fontSize: '12px', color: '#666' }}>[{show.section}]</span>}
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#999' }}>{show.seasons_count} seasons, {show.episodes_count} episodes</span>
                    </div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button onClick={() => setEditingShow(show)} style={{ padding: '4px 8px', fontSize: '12px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', background: 'white' }}>Edit</button>
                      <button onClick={() => { setSelectedShowId(show.id); setTab('episodes'); }} style={{ padding: '4px 8px', fontSize: '12px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', background: 'white' }}>Episodes</button>
                      <button onClick={() => { if (confirm('Delete this show?')) deleteShowMutation.mutate(show.id); }} style={{ padding: '4px 8px', fontSize: '12px', border: '1px solid #fcc', borderRadius: '4px', cursor: 'pointer', background: 'white', color: '#c00' }}>Delete</button>
                    </div>
                  </div>
                ))}
                {(!showsData?.items || showsData.items.length === 0) && <p style={{ padding: '24px', textAlign: 'center', color: '#999' }}>No shows found.</p>}
              </div>
            )}

            {/* Pagination */}
            {showsData && showsData.pages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
                <button disabled={page <= 1} onClick={() => setPage(page - 1)} style={{ padding: '6px 12px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', opacity: page <= 1 ? 0.5 : 1 }}>Previous</button>
                <span style={{ padding: '6px 12px' }}>Page {page} of {showsData.pages}</span>
                <button disabled={page >= showsData.pages} onClick={() => setPage(page + 1)} style={{ padding: '6px 12px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', opacity: page >= showsData.pages ? 0.5 : 1 }}>Next</button>
              </div>
            )}
          </div>
        )}

        {/* Episodes Tab */}
        {tab === 'episodes' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2>Episodes {selectedShowId && <button onClick={() => setSelectedShowId(null)} style={{ fontSize: '12px', marginLeft: '8px', padding: '4px 8px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', background: 'white' }}>Clear filter</button>}</h2>
              <button onClick={() => setShowingCreateEpisode(true)} style={{ padding: '8px 16px', background: '#4f46e5', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>+ New Episode</button>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
              <input placeholder="Search episodes..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px', width: '200px' }} />
              <select value={languageFilter} onChange={(e) => { setLanguageFilter(e.target.value); setPage(1); }} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
                <option value="">All Languages</option>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
              </select>
              <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
                <option value="">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="published">Published</option>
              </select>
            </div>

            {showingCreateEpisode && <EpisodeForm showId={selectedShowId || undefined} onSave={(data) => createEpisodeMutation.mutate(data)} onCancel={() => setShowingCreateEpisode(false)} />}
            {editingEpisode && <EpisodeForm episode={editingEpisode} showId={selectedShowId || undefined} onSave={(data) => updateEpisodeMutation.mutate({ id: editingEpisode.id, data })} onCancel={() => setEditingEpisode(null)} />}

            {episodesLoading ? <p>Loading...</p> : (
              <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden' }}>
                {(episodesData?.items || []).map((ep: Episode) => (
                  <div key={ep.id} style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{ep.title}</strong>
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#999' }}>S{ep.season_id}E{ep.episode_number}</span>
                      <span style={{ marginLeft: '8px', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', background: ep.status === 'published' ? '#dcfce7' : '#f3f4f6', color: ep.status === 'published' ? '#166534' : '#666' }}>{ep.status}</span>
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#666' }}>{ep.language}</span>
                      {ep.duration_seconds && <span style={{ marginLeft: '8px', fontSize: '12px', color: '#999' }}>{Math.floor(ep.duration_seconds / 60)}m {ep.duration_seconds % 60}s</span>}
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#999' }}>cg: {ep.content_group}</span>
                      {ep.artworks.length > 0 && <span style={{ marginLeft: '8px', fontSize: '11px', color: '#16a34a' }}>({ep.artworks.length} artwork{ep.artworks.length > 1 ? 's' : ''})</span>}
                      {ep.artworks.length === 0 && <span style={{ marginLeft: '8px', fontSize: '11px', color: '#c00' }}>(no artwork)</span>}
                    </div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button onClick={() => setEditingEpisode(ep)} style={{ padding: '4px 8px', fontSize: '12px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', background: 'white' }}>Edit</button>
                      <button onClick={() => { if (confirm('Delete this episode?')) deleteEpisodeMutation.mutate(ep.id); }} style={{ padding: '4px 8px', fontSize: '12px', border: '1px solid #fcc', borderRadius: '4px', cursor: 'pointer', background: 'white', color: '#c00' }}>Delete</button>
                    </div>
                  </div>
                ))}
                {(!episodesData?.items || episodesData.items.length === 0) && <p style={{ padding: '24px', textAlign: 'center', color: '#999' }}>No episodes found.</p>}
              </div>
            )}

            {episodesData && episodesData.pages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
                <button disabled={page <= 1} onClick={() => setPage(page - 1)} style={{ padding: '6px 12px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', opacity: page <= 1 ? 0.5 : 1 }}>Previous</button>
                <span style={{ padding: '6px 12px' }}>Page {page} of {episodesData.pages}</span>
                <button disabled={page >= episodesData.pages} onClick={() => setPage(page + 1)} style={{ padding: '6px 12px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', opacity: page >= episodesData.pages ? 0.5 : 1 }}>Next</button>
              </div>
            )}
          </div>
        )}

        {/* Publish Tab */}
        {tab === 'publish' && (
          <div>
            <h2 style={{ marginBottom: '16px' }}>Publish Catalogue</h2>

            {/* Validation Report */}
            {validation && (
              <div style={{ background: 'white', padding: '24px', borderRadius: '8px', marginBottom: '16px' }}>
                <h3 style={{ marginBottom: '12px' }}>Validation Report</h3>
                {validation.total_blocking > 0 ? (
                  <div style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: '12px', borderRadius: '4px', marginBottom: '12px' }}>
                    <p style={{ color: '#991b1b', fontWeight: 600 }}>Publishing is blocked by {validation.total_blocking} issue(s).</p>
                  </div>
                ) : (
                  <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '12px', borderRadius: '4px', marginBottom: '12px' }}>
                    <p style={{ color: '#166534', fontWeight: 600 }}>Ready to publish</p>
                  </div>
                )}

                {/* Show issues */}
                {validation.issues.shows.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h4 style={{ color: '#991b1b', marginBottom: '4px' }}>Shows ({validation.issues.shows.length})</h4>
                    {validation.issues.shows.map((issue, i) => (
                      <p key={i} style={{ fontSize: '13px', color: '#666', marginLeft: '16px' }}>- {issue.message}</p>
                    ))}
                  </div>
                )}

                {/* Episode issues */}
                {validation.issues.episodes.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h4 style={{ color: '#991b1b', marginBottom: '4px' }}>Episodes ({validation.issues.episodes.length})</h4>
                    {validation.issues.episodes.map((issue, i) => (
                      <p key={i} style={{ fontSize: '13px', color: '#666', marginLeft: '16px' }}>- {issue.message}</p>
                    ))}
                  </div>
                )}

                {/* Artwork issues */}
                {validation.issues.artwork.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h4 style={{ color: '#991b1b', marginBottom: '4px' }}>Artwork ({validation.issues.artwork.length})</h4>
                    {validation.issues.artwork.map((issue, i) => (
                      <p key={i} style={{ fontSize: '13px', color: '#666', marginLeft: '16px' }}>- {issue.message}</p>
                    ))}
                  </div>
                )}

                {/* Duplicate issues */}
                {validation.issues.duplicates.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h4 style={{ color: '#991b1b', marginBottom: '4px' }}>Duplicates ({validation.issues.duplicates.length})</h4>
                    {validation.issues.duplicates.map((issue, i) => (
                      <p key={i} style={{ fontSize: '13px', color: '#666', marginLeft: '16px' }}>- {issue.message}</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Publish Button */}
            <div style={{ background: 'white', padding: '24px', borderRadius: '8px', marginBottom: '16px' }}>
              {user?.role !== 'admin' ? (
                <>
                  <p style={{ color: '#b45309', fontWeight: 500, marginBottom: '8px' }}>
                    Only administrators can publish the catalogue.
                  </p>
                  <p style={{ color: '#999', fontSize: '13px' }}>
                    Please ask an admin to run the publish job.
                  </p>
                </>
              ) : (
                <>
                  <button
                    onClick={() => publishMutation.mutate()}
                    disabled={validation ? validation.total_blocking > 0 : true}
                    style={{
                      padding: '12px 24px',
                      background: validation && validation.total_blocking === 0 ? '#16a34a' : '#9ca3af',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '16px',
                      cursor: validation && validation.total_blocking === 0 ? 'pointer' : 'not-allowed',
                    }}
                  >
                    {publishMutation.isPending ? 'Publishing...' : 'Publish Catalogue'}
                  </button>
                  {validation && validation.total_blocking > 0 && (
                    <p style={{ color: '#c00', marginTop: '8px', fontSize: '13px' }}>
                      Resolve the {validation.total_blocking} blocking validation issue(s) before publishing.
                    </p>
                  )}
                </>
              )}
              {publishMutation.isError && <p style={{ color: '#c00', marginTop: '8px' }}>{(publishMutation.error as Error).message}</p>}
              {publishMutation.isSuccess && <p style={{ color: '#16a34a', marginTop: '8px' }}>Catalogue published successfully!</p>}
            </div>

            {/* Publish History */}
            <div style={{ background: 'white', padding: '24px', borderRadius: '8px' }}>
              <h3 style={{ marginBottom: '12px' }}>Publish History</h3>
              {runs.length === 0 ? (
                <p style={{ color: '#999' }}>No publish runs yet.</p>
              ) : (
                <div style={{ overflow: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                        <th style={{ textAlign: 'left', padding: '8px' }}>ID</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Status</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Shows</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Episodes</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Version</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Started</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Completed</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Errors</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runs.map((run: PublishRun) => (
                        <tr key={run.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                          <td style={{ padding: '8px' }}>#{run.id}</td>
                          <td style={{ padding: '8px' }}><span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '11px', background: run.status === 'success' ? '#dcfce7' : '#fee2e2', color: run.status === 'success' ? '#166534' : '#991b1b' }}>{run.status}</span></td>
                          <td style={{ padding: '8px' }}>{run.shows_count}</td>
                          <td style={{ padding: '8px' }}>{run.episodes_count}</td>
                          <td style={{ padding: '8px' }}>{run.catalogue_version || '-'}</td>
                          <td style={{ padding: '8px' }}>{new Date(run.started_at).toLocaleString()}</td>
                          <td style={{ padding: '8px' }}>{run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}</td>
                          <td style={{ padding: '8px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{run.errors || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
