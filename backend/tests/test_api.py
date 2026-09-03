import os
import sys
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.auth import hash_password, create_access_token
from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode
from app.models.artwork import Artwork
from app.storage import get_storage_backend, LocalStorageBackend

TEST_DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://peblo:peblo@localhost:5432/peblo_tv_test")
TEST_STORAGE_PATH = os.getenv("STORAGE_PATH", "/tmp/test-storage-peblo")

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    os.makedirs(TEST_STORAGE_PATH, exist_ok=True)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def admin_user():
    async with TestSessionLocal() as session:
        user = User(
            email="admin@test.local",
            username="admin_test",
            password_hash=hash_password("Admin123!"),
            role=UserRole.admin,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def editor_user():
    async with TestSessionLocal() as session:
        user = User(
            email="editor@test.local",
            username="editor_test",
            password_hash=hash_password("Editor123!"),
            role=UserRole.editor,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def admin_token(admin_user):
    return create_access_token({"sub": str(admin_user.id), "role": admin_user.role})


@pytest_asyncio.fixture
async def editor_token(editor_user):
    return create_access_token({"sub": str(editor_user.id), "role": editor_user.role})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ===== AUTH TESTS =====
@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with TestSessionLocal() as session:
            user = User(
                email="test@test.local", username="test_user",
                password_hash=hash_password("Pass123!"), role=UserRole.editor,
            )
            session.add(user)
            await session.commit()

        response = await client.post("/auth/login", json={
            "email": "test@test.local", "username": "test_user", "password": "Pass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@test.local"


@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with TestSessionLocal() as session:
            user = User(
                email="test@test.local", username="test_user",
                password_hash=hash_password("Pass123!"), role=UserRole.editor,
            )
            session.add(user)
            await session.commit()

        response = await client.post("/auth/login", json={
            "email": "test@test.local", "username": "test_user", "password": "WrongPassword"
        })
        assert response.status_code == 401


# ===== SHOW TESTS =====
@pytest.mark.asyncio
async def test_create_show(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/shows", json={
            "title": "Test Show",
            "section": "featured",
            "categories": ["adventure"],
            "status": "draft",
        }, headers=auth_header(admin_token))
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Show"
        assert data["section"] == "featured"


@pytest.mark.asyncio
async def test_create_show_invalid_section(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/shows", json={
            "title": "Test Show",
            "section": "invalid_section",
        }, headers=auth_header(admin_token))
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_editor_can_create_show(editor_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/shows", json={
            "title": "Editor Show",
            "section": "series",
        }, headers=auth_header(editor_token))
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_unauthenticated_cannot_create_show():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/shows", json={"title": "Test"})
        assert response.status_code == 403


# ===== ARTWORK VALIDATION TESTS =====
@pytest.mark.asyncio
async def test_artwork_upload_valid(admin_token):
    from app.validation import validate_artwork
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (600, 900), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()

    result = validate_artwork(data, "poster", "test.jpg")
    assert result["valid"] is True
    assert result["width"] == 600
    assert result["height"] == 900


@pytest.mark.asyncio
async def test_artwork_wrong_ratio():
    from app.validation import validate_artwork
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (600, 600), color="blue")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()

    result = validate_artwork(data, "poster", "test.jpg")
    assert result["valid"] is False
    assert any("ratio" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_artwork_too_large():
    from app.validation import validate_artwork
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (600, 900), color="green")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=100)
    data = buf.getvalue()

    data = data + b"\x00" * (200 * 1024 - len(data) + 1)

    result = validate_artwork(data, "poster", "test.jpg")
    assert result["valid"] is False
    assert any("large" in e.lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_artwork_banner_valid():
    from app.validation import validate_artwork
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (1280, 720), color="yellow")
    buf = BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    result = validate_artwork(data, "banner", "banner.png")
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_artwork_thumbnail_valid():
    from app.validation import validate_artwork
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (640, 360), color="cyan")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()

    result = validate_artwork(data, "thumbnail", "thumb.jpg")
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_artwork_invalid_dimensions():
    from app.validation import validate_artwork
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (100, 100), color="white")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()

    result = validate_artwork(data, "thumbnail", "tiny.jpg")
    assert result["valid"] is False
    assert any("dimensions" in e.lower() or "ratio" in e.lower() for e in result["errors"])


# ===== CONTENT GROUP TESTS =====
@pytest.mark.asyncio
async def test_duplicate_content_group_language_rejected(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        show_resp = await client.post("/admin/shows", json={
            "title": "Dup Show", "section": "featured"
        }, headers=auth_header(admin_token))
        show_id = show_resp.json()["id"]

        season_resp = await client.post("/admin/seasons", json={
            "show_id": show_id, "season_number": 1
        }, headers=auth_header(admin_token))
        season_id = season_resp.json()["id"]

        resp1 = await client.post("/admin/episodes", json={
            "season_id": season_id, "title": "Ep 1", "episode_number": 1,
            "language": "en", "content_group": "dup-cg-001", "status": "draft"
        }, headers=auth_header(admin_token))
        assert resp1.status_code == 201

        resp2 = await client.post("/admin/episodes", json={
            "season_id": season_id, "title": "Ep 1 dup", "episode_number": 1,
            "language": "en", "content_group": "dup-cg-001", "status": "draft"
        }, headers=auth_header(admin_token))
        assert resp2.status_code == 409


# ===== PUBLISH TESTS =====
@pytest.mark.asyncio
async def test_publish_requires_admin(editor_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/admin/catalog/publish", headers=auth_header(editor_token))
        assert response.status_code == 403


async def _create_artwork_for_episode(session, episode_id):
    from PIL import Image
    from io import BytesIO
    import tempfile

    storage = get_storage_backend()
    for artwork_type, (w, h) in [("poster", (600, 900)), ("banner", (1280, 720)), ("thumbnail", (640, 360))]:
        img = Image.new("RGB", (w, h), color="red")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        img_bytes = buf.getvalue()

        filename = f"test_{artwork_type}_{episode_id}.jpg"
        path = await storage.save(filename, img_bytes, "image/jpeg")

        artwork = Artwork(
            episode_id=episode_id,
            artwork_type=artwork_type,
            storage_key=path,
            original_filename=filename,
            file_size=len(img_bytes),
            width=w,
            height=h,
            mime_type="image/jpeg",
        )
        session.add(artwork)
    await session.commit()


@pytest.mark.asyncio
async def test_publish_blocks_when_validation_fails(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        show_resp = await client.post("/admin/shows", json={
            "title": "Block Show", "section": "featured", "status": "published"
        }, headers=auth_header(admin_token))
        show_id = show_resp.json()["id"]

        season_resp = await client.post("/admin/seasons", json={
            "show_id": show_id, "season_number": 1
        }, headers=auth_header(admin_token))
        season_id = season_resp.json()["id"]

        ep_resp = await client.post("/admin/episodes", json={
            "season_id": season_id, "title": "Ep 1", "episode_number": 1,
            "language": "en", "content_group": "block-ep-001",
            "duration_seconds": 300, "status": "published"
        }, headers=auth_header(admin_token))

        response = await client.post("/admin/catalog/publish", headers=auth_header(admin_token))
        assert response.status_code == 422
        assert "blocking" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_publish_success(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        show_resp = await client.post("/admin/shows", json={
            "title": "Pub Show", "section": "featured", "status": "published"
        }, headers=auth_header(admin_token))
        show_id = show_resp.json()["id"]

        season_resp = await client.post("/admin/seasons", json={
            "show_id": show_id, "season_number": 1
        }, headers=auth_header(admin_token))
        season_id = season_resp.json()["id"]

        ep_resp = await client.post("/admin/episodes", json={
            "season_id": season_id, "title": "Ep 1", "episode_number": 1,
            "language": "en", "content_group": "pub-ep-001",
            "duration_seconds": 300, "status": "published"
        }, headers=auth_header(admin_token))
        episode_id = ep_resp.json()["id"]

        async with TestSessionLocal() as session:
            await _create_artwork_for_episode(session, episode_id)

        response = await client.post("/admin/catalog/publish", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["shows_count"] >= 1


# ===== SEARCH TESTS =====
@pytest.mark.asyncio
async def test_catalog_search(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        show_resp = await client.post("/admin/shows", json={
            "title": "Searchable Show", "section": "featured", "status": "published",
            "categories": ["adventure"]
        }, headers=auth_header(admin_token))
        show_id = show_resp.json()["id"]

        season_resp = await client.post("/admin/seasons", json={
            "show_id": show_id, "season_number": 1
        }, headers=auth_header(admin_token))
        season_id = season_resp.json()["id"]

        ep_resp = await client.post("/admin/episodes", json={
            "season_id": season_id, "title": "Adventure Episode", "episode_number": 1,
            "language": "en", "content_group": "search-ep-001",
            "duration_seconds": 300, "status": "published"
        }, headers=auth_header(admin_token))
        episode_id = ep_resp.json()["id"]

        async with TestSessionLocal() as session:
            await _create_artwork_for_episode(session, episode_id)

        await client.post("/admin/catalog/publish", headers=auth_header(admin_token))

        resp = await client.get("/catalog/search?q=adventure")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total_shows"] >= 1

        resp2 = await client.get("/catalog/search?category=adventure")
        assert resp2.status_code == 200

        resp3 = await client.get("/catalog/search?language=en")
        assert resp3.status_code == 200

        resp4 = await client.get("/catalog/search?q=adventure&language=en&category=adventure")
        assert resp4.status_code == 200


# ===== HEALTH TEST =====
@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ===== VALIDATION REPORT TESTS =====
@pytest.mark.asyncio
async def test_validation_report(admin_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/admin/validation-report", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        assert "total_blocking" in data
