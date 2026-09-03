const API_BASE = '/api';

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  return response;
}

export async function login(email: string, password: string) {
  const response = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, username: email, password }),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Login failed');
  }
  return response.json();
}

export async function getMe() {
  const response = await apiFetch('/auth/me');
  if (!response.ok) throw new Error('Not authenticated');
  return response.json();
}

export async function getShows(params: Record<string, string> = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await apiFetch(`/admin/shows?${query}`);
  if (!response.ok) throw new Error('Failed to fetch shows');
  return response.json();
}

export async function getShow(id: number) {
  const response = await apiFetch(`/admin/shows/${id}`);
  if (!response.ok) throw new Error('Failed to fetch show');
  return response.json();
}

export async function createShow(data: any) {
  const response = await apiFetch('/admin/shows', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create show');
  }
  return response.json();
}

export async function updateShow(id: number, data: any) {
  const response = await apiFetch(`/admin/shows/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to update show');
  }
  return response.json();
}

export async function deleteShow(id: number) {
  const response = await apiFetch(`/admin/shows/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete show');
}

export async function getSeasons(params: Record<string, string> = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await apiFetch(`/admin/seasons?${query}`);
  if (!response.ok) throw new Error('Failed to fetch seasons');
  return response.json();
}

export async function createSeason(data: any) {
  const response = await apiFetch('/admin/seasons', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create season');
  }
  return response.json();
}

export async function getEpisodes(params: Record<string, string> = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await apiFetch(`/admin/episodes?${query}`);
  if (!response.ok) throw new Error('Failed to fetch episodes');
  return response.json();
}

export async function getEpisode(id: number) {
  const response = await apiFetch(`/admin/episodes/${id}`);
  if (!response.ok) throw new Error('Failed to fetch episode');
  return response.json();
}

export async function createEpisode(data: any) {
  const response = await apiFetch('/admin/episodes', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create episode');
  }
  return response.json();
}

export async function updateEpisode(id: number, data: any) {
  const response = await apiFetch(`/admin/episodes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to update episode');
  }
  return response.json();
}

export async function deleteEpisode(id: number) {
  const response = await apiFetch(`/admin/episodes/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete episode');
}

export async function uploadArtwork(formData: FormData) {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/admin/artworks`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to upload artwork');
  }
  return response.json();
}

export async function deleteArtwork(id: number) {
  const response = await apiFetch(`/admin/artworks/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete artwork');
}

export async function getValidationReport() {
  const response = await apiFetch('/admin/validation-report');
  if (!response.ok) throw new Error('Failed to fetch validation report');
  return response.json();
}

export async function publishCatalog() {
  const response = await apiFetch('/admin/catalog/publish', { method: 'POST' });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to publish');
  }
  return response.json();
}

export async function getPublishRuns() {
  const response = await apiFetch('/admin/catalog/runs');
  if (!response.ok) throw new Error('Failed to fetch publish runs');
  return response.json();
}
