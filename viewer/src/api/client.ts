const API_BASE = '/api';

export async function getCatalog() {
  const response = await fetch(`${API_BASE}/catalog`);
  if (!response.ok) throw new Error('Failed to fetch catalogue');
  return response.json();
}

export async function searchCatalog(params: Record<string, string> = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE}/catalog/search?${query}`);
  if (!response.ok) throw new Error('Failed to search catalogue');
  return response.json();
}
