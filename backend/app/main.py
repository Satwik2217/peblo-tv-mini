from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import engine, Base, async_session
from app.routers import auth, shows, seasons, episodes, artworks, validation_report, catalog, catalog_public
from app.auth import hash_password
from app.models.user import User, UserRole
from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode
import json
import os
from pathlib import Path

settings = get_settings()


async def seed_database():
    from sqlalchemy import select, func
    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(func.count(User.id)))
        if result.scalar() > 0:
            return

        # Create demo users
        admin = User(
            email="admin@peblo.local",
            username="admin",
            password_hash=hash_password("Admin123!"),
            role=UserRole.admin,
        )
        editor = User(
            email="editor@peblo.local",
            username="editor",
            password_hash=hash_password("Editor123!"),
            role=UserRole.editor,
        )
        db.add_all([admin, editor])
        await db.flush()

        # Load seed data
        seed_path = Path(__file__).parent.parent.parent / "given files" / "seed_shows.json"
        if not seed_path.exists():
            # Try alternative path for Docker
            seed_path = Path("/app/given files/seed_shows.json")
        if not seed_path.exists():
            print(f"Warning: seed_shows.json not found at {seed_path}")
            return

        with open(seed_path, "r", encoding="utf-8") as f:
            episodes_data = json.load(f)

        # Group episodes by show slug
        shows_map = {}
        seasons_map = {}

        for ep_data in episodes_data:
            slug = ep_data["slug"]
            if slug not in shows_map:
                shows_map[slug] = {
                    "title": ep_data["show_title"],
                    "slug": slug,
                    "synopsis": ep_data.get("synopsis"),
                    "section": ep_data.get("section"),
                    "categories": json.dumps(ep_data.get("categories", [])),
                    "status": ep_data.get("status", "draft"),
                }

            season_key = f"{slug}_s{ep_data['season_number']}"
            if season_key not in seasons_map:
                seasons_map[season_key] = {
                    "slug": slug,
                    "season_number": ep_data["season_number"],
                    "title": f"Season {ep_data['season_number']}" if ep_data["season_number"] > 0 else "Trailers",
                }

        # Create shows
        show_objects = {}
        for slug, show_data in shows_map.items():
            show = Show(**show_data)
            db.add(show)
            await db.flush()
            await db.refresh(show)
            show_objects[slug] = show

        # Create seasons
        season_objects = {}
        for key, season_data in seasons_map.items():
            show = show_objects[season_data["slug"]]
            season = Season(
                show_id=show.id,
                season_number=season_data["season_number"],
                title=season_data.get("title"),
            )
            db.add(season)
            await db.flush()
            await db.refresh(season)
            season_objects[key] = season

        # Create episodes
        for ep_data in episodes_data:
            slug = ep_data["slug"]
            season_key = f"{slug}_s{ep_data['season_number']}"
            season = season_objects.get(season_key)
            if not season:
                continue

            # Check for duplicate content_group + language
            existing = await db.execute(
                select(Episode).where(
                    Episode.content_group == ep_data["content_group"],
                    Episode.language == ep_data["language"],
                )
            )
            if existing.scalar_one_or_none():
                continue  # Skip duplicate

            episode = Episode(
                season_id=season.id,
                title=ep_data["episode_title"],
                synopsis=ep_data.get("synopsis"),
                episode_number=ep_data["episode_number"],
                duration_seconds=ep_data.get("duration_seconds"),
                language=ep_data["language"],
                content_group=ep_data["content_group"],
                status=ep_data.get("status", "draft"),
            )
            db.add(episode)

        await db.commit()
        print(f"Seeded: {len(show_objects)} shows, {len(season_objects)} seasons, {len(episodes_data)} episodes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_database()
    # Create storage directory
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Peblo TV Mini API",
    description="CMS upload → published catalogue → Netflix-style browse",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(shows.router)
app.include_router(seasons.router)
app.include_router(episodes.router)
app.include_router(artworks.router)
app.include_router(validation_report.router)
app.include_router(catalog.router)
app.include_router(catalog_public.router)


@app.get("/health")
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": str(e)},
        )


# Serve stored files
if os.path.exists(settings.STORAGE_PATH):
    app.mount("/storage", StaticFiles(directory=settings.STORAGE_PATH), name="storage")
