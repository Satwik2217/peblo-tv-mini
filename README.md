# Peblo TV Mini

CMS upload → published catalogue → Netflix-style browse

Peblo · Full-Stack Platform Engineer Take-Home Challenge

---

## How to Run

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL | Purpose |
|---------|-----|---------|
| CMS | http://localhost:5173 | Internal content management |
| Viewer | http://localhost:5174 | Public browse UI |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger documentation |

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@peblo.local | Admin123! |
| Editor | editor@peblo.local | Editor123! |

Development only. See [Secrets Management](#secrets-management) for production.

---

## Architecture

```
CMS (React, port 5173) ──► API (FastAPI + Postgres, port 8000) ──► Publish Job
                                                                     │
                                                      catalogue.json in storage
                                                                     │
                                    Viewer UI (React, port 5174) ◄───┘
```

- **CMS** and **Viewer** are separate React apps communicating with the same FastAPI backend
- The Viewer reads **only** the published catalogue file — it never calls admin endpoints
- The CMS uses admin endpoints behind JWT authentication

### Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x (async), PostgreSQL 16, Alembic, Pydantic, JWT auth (passlib + bcrypt)
- **Frontend:** React 18, TypeScript, Vite, TanStack Query, React Router v6
- **Infrastructure:** Docker, Docker Compose, GitHub Actions
- **Storage:** Local filesystem (abstracted behind `StorageBackend` interface for R2 swap)
- **Image validation:** Pillow (aspect ratio, dimensions, file size, MIME sniffing)

---

## Seed Data

On first startup the database is seeded from `given files/seed_shows.json`:

- 8 shows across 4 sections (featured, series, minisodes, songs)
- ~95 episodes with English and Hindi language variants
- Season 0 trailers for 2 shows
- Idempotent — skips re-insertion on existing data

### Seed Data Issues Detected

The seed data is deliberately imperfect. The validation report surfaces these:

1. **Rhyme Rangers** — `section: null` (cannot publish without a section)
2. **Duplicate content group** — `ep_9001` duplicates `(motis-many-lives-s01e02, hi)` from `ep_0004`
3. **Missing artwork** — `ep_0036` (Discover India, ep 4) has `artwork_available: []`
4. **Draft episodes** — Number Nest eps 7-8 and all Rhyme Rangers are drafts
5. **Season 0 trailers** — correctly handled as separate trailer entries, not normal seasons

---

## Part A — Backend

### Schema

Shows → Seasons → Episodes (with artwork records and publish runs). Key fields:

- **Show:** title, slug, synopsis, section, categories (JSON), status (draft/published)
- **Season:** show_id, season_number, title (Season 0 = Trailers)
- **Episode:** season_id, title, synopsis, episode_number, duration_seconds, language, content_group, status
- **Artwork:** entity type (show/episode), artwork type (poster/banner/thumbnail), dimensions, storage key
- **PublishRun:** started_at, completed_at, status, shows_count, episodes_count, errors (JSON), triggered_by

Unique constraint: `(content_group, language)` across all episodes.

### Artwork Validation

Three sizes enforced per `reference.json`:

| Type | Aspect | Target | Max KB | Tolerance |
|------|--------|--------|--------|-----------|
| Poster | 2:3 | 600×900 | 200 | 5% aspect, 50% dimensions |
| Banner | 16:9 | 1280×720 | 200 | 5% aspect, 50% dimensions |
| Thumbnail | 16:9 | 640×360 | 200 | 5% aspect, 50% dimensions |

Checks performed:
1. File size ≤ 200 KB
2. Valid image (PIL verify)
3. Aspect ratio within 5% of target
4. Dimensions within 50% of target
5. MIME type detected from content bytes (not filename) — jpeg, png, webp only

Errors are returned as human-readable lines (e.g. "Poster is 600×600 — expected 2:3 ratio").

### Publishing Pipeline

`POST /admin/catalog/publish` (admin only):

1. **Validation gate** — checks `GET /admin/validation-report` first; blocks if `total_blocking > 0` (returns 422)
2. **Build catalogue** — loads all published shows/seasons/episodes, collapses `content_group` variants, groups by section
3. **Write versioned file** — `catalogue-v{run_id}.json` via storage backend
4. **Swap pointer** — atomically replaces `current.json` via `os.replace()`
5. **Record run** — updates PublishRun with counts, status, errors

Content group variants collapse into one entry with a `languages` list. Season 0 is treated as trailers. Duplicate languages within a content group are de-duplicated (first occurrence kept, logged as non-blocking error).

### API Endpoints

**Public (no auth):**
- `GET /health` — health check with database connectivity
- `GET /catalog` — published catalogue JSON
- `GET /catalog/search?q=&category=&language=&section=` — server-side search, all filters compose

**Auth:**
- `POST /auth/login` — JWT token
- `POST /auth/register` — create user
- `GET /auth/me` — current user

**Admin CRUD (editor or admin):**
- `GET/POST /admin/shows` — list/create
- `GET/PUT/DELETE /admin/shows/{id}` — get/update/delete
- `GET/POST /admin/seasons` — list/create
- `GET/PUT/DELETE /admin/seasons/{id}` — get/update/delete
- `GET/POST /admin/episodes` — list/create
- `GET/PUT/DELETE /admin/episodes/{id}` — get/update/delete
- `POST /admin/artworks` — upload (multipart, server-validated)
- `DELETE /admin/artworks/{id}` — delete

**Admin only:**
- `POST /admin/catalog/publish` — publish catalogue (403 if not admin)
- `GET /admin/validation-report` — blocking issues report
- `GET /admin/catalog/runs` — publish run history

### Role Enforcement

Roles are enforced server-side via FastAPI dependencies (`require_admin`, `require_editor_or_admin`). The user's role is read from the database on every request, not from the JWT claim. An editor calling the publish endpoint receives 403.

**Known weakness:** The `/auth/register` endpoint accepts a client-supplied `role` field, meaning anyone can self-register as admin. In production, registration would be restricted or role assignment would be admin-only. This is documented as a deliberate trade-off for the demo.

### Tests

```bash
cd backend
export DATABASE_URL=postgresql+asyncpg://peblo:peblo@localhost:5432/peblo_tv_test
python -m pytest tests/ -v
```

Tests cover: login, RBAC (admin vs editor vs unauthenticated → 403), artwork validation (correct/wrong ratio/oversized/invalid dimensions), duplicate content_group+language → 409, publish requires admin (403), publish blocked by validation (422), publish success, catalog search, health endpoint, validation report.

---

## Part B — Internal CMS

React + TypeScript app at `localhost:5173`.

### Features

- **Shows tab** — list with search, section filter, status filter, pagination, create/edit/delete
- **Episodes tab** — list with search, language filter, status filter, per-show filter, pagination, create/edit/delete
- **Publish tab** — validation report (blocking vs non-blocking), admin-only publish button (disabled with reasons when blocked), publish run history
- **Artwork upload** — three labelled slots (poster/banner/thumbnail) showing required dimensions, live preview, human-readable errors on rejection

### States Handled

- **Loading** — spinner/text on data fetch
- **Empty** — "No shows found" / "No episodes found" messages
- **Error** — mutation errors displayed, login failures shown in red banner
- **Permission denied** — publish button hidden for editors, 403 responses handled

### Styling

Inline styles for simplicity. Usable by a content editor — clear labels, validation feedback, pagination for large lists. Not beautiful, but functional for someone doing this 50 times a week.

---

## Part C — Viewer Browse UI

React + TypeScript app at `localhost:5174`. Reads **only** the published catalogue — no admin endpoints called.

### Features

- **Home** — hero banner (featured show, banner artwork), horizontal rows by section (poster artwork), scrollable with momentum on mobile
- **Show detail** — synopsis, seasons with episodes (thumbnail artwork), language variant buttons, Season 0 trailers shown separately
- **Search** — text search + category/language/section filter dropdowns, sensible empty state
- **Responsive** — clamp-based padding/sizing, flex-wrap on filters, scrollable rows

### Artwork Per Surface

- Hero banner: `banner` (16:9)
- Row cards: `poster` (2:3)
- Episode lists: `thumbnail` (16:9)

### States Handled

- Loading skeleton with pulse animation
- Empty catalogue message
- Image load errors (fallback "No Image")
- Slow image loading (opacity transition)

---

## Part D — Pipeline & Operability

### Docker Compose

`docker-compose up` brings up: PostgreSQL, FastAPI (with auto-seeding), CMS, and Viewer. First try, no manual steps.

### GitHub Actions CI

`.github/workflows/ci.yml` runs on push/PR to main:

1. **Backend lint** — ruff check
2. **Backend tests** — pytest with PostgreSQL service container
3. **Frontend build** — TypeScript check + Vite build for CMS and Viewer
4. **Docker build** — validates all images build

### Deploy Step (written, not executed)

The deploy step is configured for Docker Compose deployment. For cloud deployment (e.g., AWS ECS or Kubernetes), you would:
1. Push images to a registry (ECR, Docker Hub)
2. Update service definitions with new image tags
3. Run database migrations before deploying the new API
4. Use a health check gate before switching traffic

### Secrets Management

All variables documented in `.env.example`:

| Variable | Purpose | Production Guidance |
|----------|---------|-------------------|
| `DATABASE_URL` | PostgreSQL connection | Use secrets manager (Vault, AWS SM) |
| `JWT_SECRET` | Token signing key | Strong random value, 32+ bytes, rotated regularly |
| `STORAGE_BACKEND` | Storage type | Switch to `r2` for production |
| `STORAGE_PATH` | Local storage dir | Not used with R2 |
| `CORS_ORIGINS` | Allowed origins | Lock down to production domains |

### Health Endpoint & Alerting

`GET /health` checks database connectivity and returns `{status, database}`.

**Recommended alert: Publish failures.** A failed publish means the viewer shows stale content. Content editors cannot fix this without engineering help. Monitor `POST /admin/catalog/publish` response codes — alert on 5xx or repeated 422 (validation blocking).

---

## Part E — Written Reasoning

### 1. Atomic Publishing

Publishing is atomic via a pointer-swap pattern:

1. Write the full catalogue to a versioned file: `catalogue-v{run_id}.json`
2. Atomically replace `current.json` (a tiny pointer file) via `os.replace()`
3. Readers always dereference `current.json` first, then follow the pointer

Each individual write is made atomic by the storage backend (temp file + `os.replace()`). The two writes are **not** a cross-file transaction — but the safety property holds because:
- Readers always go through `current.json`
- A crash between writes leaves the previous valid pointer intact
- The incomplete versioned file sits on disk but is never pointed to

**If the process dies mid-publish:** The old catalogue remains live. The incomplete file is orphaned. On next successful publish, a new versioned file is written and the pointer is swapped. No data corruption, no half-written catalogue visible to readers.

### 2. Storage Abstraction

`StorageBackend` is an abstract class with: `save`, `read`, `delete`, `exists`, `public_url`, `generate_key`. The only implementation is `LocalStorageBackend`.

**To move to Cloudflare R2:**
1. Create `R2StorageBackend` implementing `StorageBackend`
2. Use `boto3` (S3-compatible API) for `save`/`read`/`delete`/`exists`
3. `public_url()` returns the R2 public domain URL
4. `generate_key()` produces the R2 object key
5. Update `get_storage_backend()` to check `STORAGE_BACKEND=r2` env var
6. No business logic changes — all code interacts through the abstraction

### 3. Search

The `GET /catalog/search` endpoint loads the published catalogue JSON and performs server-side filtering:
- `q` matches show title, episode title, and category (case-insensitive substring)
- `category`, `language`, `section` are exact-match filters
- All filters compose with AND logic

**Scale limits:**
- ~100 episodes (current): instant, sub-millisecond
- ~10K episodes: ~50ms, still acceptable
- ~100K episodes: ~500ms, becomes sluggish
- ~1M+ episodes: not viable with JSON parsing

**At larger scale, I would:**
1. PostgreSQL full-text search with GIN indexes (first step up, handles most needs)
2. PostgreSQL trigram indexes (`pg_trgm`) for fuzzy matching
3. Elasticsearch/OpenSearch for complex query needs and sub-100ms latency at scale

### 4. Why a Pre-Published Catalogue?

**Benefits:**
- Predictable viewer reads — single file, consistent snapshot
- Decoupling — viewer doesn't depend on database availability
- CDN-cacheable — catalogue can be aggressively cached at the edge
- Zero DB load per viewer request
- Consistent state — every viewer sees the same version

**Where it bites:**
- Content isn't live until publishing — editors must explicitly publish (delayed updates)
- Catalogue generation cost — full rebuild on every publish (no incremental)
- Search is limited to what's in the JSON file (no real-time indexing)
- No real-time updates — changes require a publish cycle
- The viewer can show stale data if the last publish was old

### 5. What I Left Out and Why

| Item | Why Skipped |
|------|-------------|
| Catalogue rollback | Implemented publish runs but not version rollback. Would add with a pointer history file and a `rollback-to` endpoint. Time constraint. |
| Publish dry-run diff | Would show what changed between versions. Important for production but not core to the demo. |
| Audit log | No tracking of who changed what. Would add with a `change_events` table. Not required for the mini scope. |
| Real cloud deployment | Docker Compose only. No Kubernetes/Terraform. The deploy step is written and explained in CI. |
| R2 implementation | Abstraction exists and is clean, but only local storage is implemented. Swapping is one class. |
| Advanced search engine | JSON-based server-side search. Adequate for ~100 episodes. Would use PostgreSQL FTS or Elasticsearch at scale. |
| Rate limiting | Appropriate for demo. Would add in production with slowapi or similar. |
| HTTPS | Development only. Production would use TLS termination at load balancer. |
| User management UI | Users are seeded. No admin UI for user CRUD. Would add for production. |
| Video playback | This is a catalogue/browse system only. |

### AI Tools Used

AI assistance was used throughout this project:

- **Architecture planning** — initial data model design, API structure, storage abstraction pattern
- **Code generation** — boilerplate for FastAPI routes, React components, Docker configuration, CI workflow
- **Error handling patterns** — consistent error response formats across endpoints
- **Validation logic** — artwork dimension/aspect-ratio checking with Pillow
- **Frontend styling** — inline style patterns for Netflix-style UI components

**Where I accepted AI output:** Boilerplate code, standard patterns (CRUD, auth, Docker), validation logic where specs were clear.

**Where I rejected or modified AI output:** All architectural decisions (atomic publishing pattern, pointer-swap vs file locking, storage abstraction design). Seed data analysis and imperfection detection. Publish pipeline error handling (non-blocking vs blocking errors). Authentication role enforcement patterns. Final integration and bug fixes.

---

## Trade-offs

| Decision | Chose | Trade-off |
|----------|-------|-----------|
| JSON catalogue vs DB queries | JSON file | Fast, cacheable, decoupled — but delayed updates, no real-time |
| Local storage vs cloud | Local disk | Simple for demo — but R2 swap is one class away |
| Inline styles vs CSS framework | Inline styles | Zero config, works immediately — but harder to maintain at scale |
| Open registration | Accept for demo | Allows easy testing — but undermines RBAC in production |
| Full rebuild vs incremental publish | Full rebuild | Simple, consistent — but slow at large catalogue size |
| JSON search vs search engine | JSON filter | Adequate for ~100 episodes — but won't scale |

---

## Time Spent

| Section | Hours |
|---------|-------|
| Discovery & Architecture | 0.5h |
| Backend (models, auth, CRUD, validation) | 2.0h |
| Publishing pipeline & storage abstraction | 1.0h |
| Artwork validation & upload | 0.5h |
| CMS frontend | 1.5h |
| Viewer frontend | 1.0h |
| Docker & infrastructure | 0.5h |
| Tests | 0.5h |
| README & documentation | 0.5h |
| **Total** | **~8h** |

---

## Suggested Demo Flow

1. `docker compose up --build`
2. Open CMS → http://localhost:5173
3. Login as **editor** — browse shows, note seeded data
4. Open Publish tab — review validation report, see blocking issues
5. Note publish button is disabled for editors
6. Try uploading artwork with wrong dimensions — see editor-readable error
7. Login as **admin** — publish button is now enabled
8. Publish the catalogue
9. Open Viewer → http://localhost:5174
10. Hero banner, horizontal rows, show detail with language variants
11. Search page — text search, category/language filters, empty state
12. Note Season 0 trailers handled separately
