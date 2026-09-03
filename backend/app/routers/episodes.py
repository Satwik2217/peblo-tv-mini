import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.models.episode import Episode
from app.models.season import Season
from app.models.artwork import Artwork
from app.schemas.episode import EpisodeCreate, EpisodeUpdate, EpisodeResponse, EpisodeListResponse
from app.auth import require_editor_or_admin
from app.models.user import User

router = APIRouter(prefix="/admin/episodes", tags=["admin-episodes"])


@router.get("", response_model=EpisodeListResponse)
async def list_episodes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    language: Optional[str] = None,
    status_filter: Optional[str] = None,
    show_id: Optional[int] = None,
    season_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    query = select(Episode).join(Season)
    count_query = select(func.count(Episode.id)).join(Season)

    if show_id:
        query = query.where(Season.show_id == show_id)
        count_query = count_query.where(Season.show_id == show_id)

    if season_id:
        query = query.where(Episode.season_id == season_id)
        count_query = count_query.where(Episode.season_id == season_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(or_(Episode.title.ilike(search_pattern), Episode.content_group.ilike(search_pattern)))
        count_query = count_query.where(or_(Episode.title.ilike(search_pattern), Episode.content_group.ilike(search_pattern)))

    if language:
        query = query.where(Episode.language == language)
        count_query = count_query.where(Episode.language == language)

    if status_filter:
        query = query.where(Episode.status == status_filter)
        count_query = count_query.where(Episode.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * page_size
    query = query.order_by(Episode.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    episodes = result.scalars().all()

    items = []
    for ep in episodes:
        artworks_result = await db.execute(select(Artwork).where(Artwork.episode_id == ep.id))
        artworks = artworks_result.scalars().all()
        artworks_list = [
            {"id": a.id, "artwork_type": a.artwork_type, "storage_key": a.storage_key, "width": a.width, "height": a.height}
            for a in artworks
        ]
        items.append(EpisodeResponse(
            id=ep.id, season_id=ep.season_id, title=ep.title, synopsis=ep.synopsis,
            episode_number=ep.episode_number, duration_seconds=ep.duration_seconds,
            language=ep.language, content_group=ep.content_group,
            status=ep.status.value if hasattr(ep.status, 'value') else ep.status,
            created_at=ep.created_at, updated_at=ep.updated_at, artworks=artworks_list,
        ))

    return EpisodeListResponse(
        items=items, total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode(
    episode_data: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    season_result = await db.execute(select(Season).where(Season.id == episode_data.season_id))
    if not season_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Season not found")

    existing = await db.execute(
        select(Episode).where(
            Episode.content_group == episode_data.content_group,
            Episode.language == episode_data.language,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Episode with content_group '{episode_data.content_group}' and language '{episode_data.language}' already exists.",
        )

    episode = Episode(
        season_id=episode_data.season_id,
        title=episode_data.title,
        synopsis=episode_data.synopsis,
        episode_number=episode_data.episode_number,
        duration_seconds=episode_data.duration_seconds,
        language=episode_data.language,
        content_group=episode_data.content_group,
        status=episode_data.status,
    )
    db.add(episode)
    await db.flush()
    await db.refresh(episode)
    return EpisodeResponse(
        id=episode.id, season_id=episode.season_id, title=episode.title, synopsis=episode.synopsis,
        episode_number=episode.episode_number, duration_seconds=episode.duration_seconds,
        language=episode.language, content_group=episode.content_group,
        status=episode.status.value if hasattr(episode.status, 'value') else episode.status,
        created_at=episode.created_at, updated_at=episode.updated_at,
    )


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    artworks_result = await db.execute(select(Artwork).where(Artwork.episode_id == ep.id))
    artworks = artworks_result.scalars().all()
    artworks_list = [
        {"id": a.id, "artwork_type": a.artwork_type, "storage_key": a.storage_key, "width": a.width, "height": a.height}
        for a in artworks
    ]
    return EpisodeResponse(
        id=ep.id, season_id=ep.season_id, title=ep.title, synopsis=ep.synopsis,
        episode_number=ep.episode_number, duration_seconds=ep.duration_seconds,
        language=ep.language, content_group=ep.content_group,
        status=ep.status.value if hasattr(ep.status, 'value') else ep.status,
        created_at=ep.created_at, updated_at=ep.updated_at, artworks=artworks_list,
    )


@router.put("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: int,
    episode_data: EpisodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")

    if episode_data.title is not None:
        ep.title = episode_data.title
    if episode_data.synopsis is not None:
        ep.synopsis = episode_data.synopsis
    if episode_data.episode_number is not None:
        ep.episode_number = episode_data.episode_number
    if episode_data.duration_seconds is not None:
        ep.duration_seconds = episode_data.duration_seconds
    if episode_data.language is not None:
        ep.language = episode_data.language
    if episode_data.content_group is not None:
        ep.content_group = episode_data.content_group
    if episode_data.status is not None:
        ep.status = episode_data.status

    await db.flush()
    await db.refresh(ep)
    return EpisodeResponse(
        id=ep.id, season_id=ep.season_id, title=ep.title, synopsis=ep.synopsis,
        episode_number=ep.episode_number, duration_seconds=ep.duration_seconds,
        language=ep.language, content_group=ep.content_group,
        status=ep.status.value if hasattr(ep.status, 'value') else ep.status,
        created_at=ep.created_at, updated_at=ep.updated_at,
    )


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    await db.delete(ep)
    await db.flush()
