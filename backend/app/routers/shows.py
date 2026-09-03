import json
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.models.show import Show, VALID_SECTIONS, VALID_CATEGORIES
from app.models.season import Season
from app.models.episode import Episode
from app.schemas.show import ShowCreate, ShowUpdate, ShowResponse, ShowListResponse
from app.auth import require_editor_or_admin
from app.models.user import User
import re

router = APIRouter(prefix="/admin/shows", tags=["admin-shows"])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


@router.get("", response_model=ShowListResponse)
async def list_shows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    section: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    query = select(Show)
    count_query = select(func.count(Show.id))

    if search:
        search_pattern = f"%{search}%"
        query = query.where(or_(Show.title.ilike(search_pattern), Show.synopsis.ilike(search_pattern)))
        count_query = count_query.where(or_(Show.title.ilike(search_pattern), Show.synopsis.ilike(search_pattern)))

    if section:
        query = query.where(Show.section == section)
        count_query = count_query.where(Show.section == section)

    if status_filter:
        query = query.where(Show.status == status_filter)
        count_query = count_query.where(Show.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * page_size
    query = query.order_by(Show.updated_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    shows = result.scalars().all()

    items = []
    for show in shows:
        seasons_count_result = await db.execute(select(func.count(Season.id)).where(Season.show_id == show.id))
        seasons_count = seasons_count_result.scalar() or 0
        episodes_count_result = await db.execute(
            select(func.count(Episode.id))
            .join(Season)
            .where(Season.show_id == show.id)
        )
        episodes_count = episodes_count_result.scalar() or 0
        categories = json.loads(show.categories) if show.categories else []
        items.append(ShowResponse(
            id=show.id,
            title=show.title,
            slug=show.slug,
            synopsis=show.synopsis,
            section=show.section,
            categories=categories,
            status=show.status.value if hasattr(show.status, 'value') else show.status,
            created_at=show.created_at,
            updated_at=show.updated_at,
            seasons_count=seasons_count,
            episodes_count=episodes_count,
        ))

    return ShowListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
async def create_show(
    show_data: ShowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    if show_data.section and show_data.section not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section: {show_data.section}. Valid: {VALID_SECTIONS}")

    if show_data.categories:
        invalid_cats = [c for c in show_data.categories if c not in VALID_CATEGORIES]
        if invalid_cats:
            raise HTTPException(status_code=400, detail=f"Invalid categories: {invalid_cats}. Valid: {VALID_CATEGORIES}")

    slug = show_data.slug or slugify(show_data.title)

    existing = await db.execute(select(Show).where(Show.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"A show with slug '{slug}' already exists.")

    show = Show(
        title=show_data.title,
        slug=slug,
        synopsis=show_data.synopsis,
        section=show_data.section,
        categories=json.dumps(show_data.categories) if show_data.categories else None,
        status=show_data.status,
    )
    db.add(show)
    await db.flush()
    await db.refresh(show)
    categories = json.loads(show.categories) if show.categories else []
    return ShowResponse(
        id=show.id, title=show.title, slug=show.slug, synopsis=show.synopsis,
        section=show.section, categories=categories,
        status=show.status.value if hasattr(show.status, 'value') else show.status,
        created_at=show.created_at, updated_at=show.updated_at,
    )


@router.get("/{show_id}", response_model=ShowResponse)
async def get_show(
    show_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    categories = json.loads(show.categories) if show.categories else []
    seasons_count_result = await db.execute(select(func.count(Season.id)).where(Season.show_id == show.id))
    seasons_count = seasons_count_result.scalar() or 0
    episodes_count_result = await db.execute(
        select(func.count(Episode.id)).join(Season).where(Season.show_id == show.id)
    )
    episodes_count = episodes_count_result.scalar() or 0
    return ShowResponse(
        id=show.id, title=show.title, slug=show.slug, synopsis=show.synopsis,
        section=show.section, categories=categories,
        status=show.status.value if hasattr(show.status, 'value') else show.status,
        created_at=show.created_at, updated_at=show.updated_at,
        seasons_count=seasons_count, episodes_count=episodes_count,
    )


@router.put("/{show_id}", response_model=ShowResponse)
async def update_show(
    show_id: int,
    show_data: ShowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    if show_data.title is not None:
        show.title = show_data.title
    if show_data.slug is not None:
        show.slug = show_data.slug
    if show_data.synopsis is not None:
        show.synopsis = show_data.synopsis
    if show_data.section is not None:
        if show_data.section not in VALID_SECTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid section: {show_data.section}. Valid: {VALID_SECTIONS}")
        show.section = show_data.section
    if show_data.categories is not None:
        invalid_cats = [c for c in show_data.categories if c not in VALID_CATEGORIES]
        if invalid_cats:
            raise HTTPException(status_code=400, detail=f"Invalid categories: {invalid_cats}. Valid: {VALID_CATEGORIES}")
        show.categories = json.dumps(show_data.categories)
    if show_data.status is not None:
        show.status = show_data.status

    await db.flush()
    await db.refresh(show)
    categories = json.loads(show.categories) if show.categories else []
    return ShowResponse(
        id=show.id, title=show.title, slug=show.slug, synopsis=show.synopsis,
        section=show.section, categories=categories,
        status=show.status.value if hasattr(show.status, 'value') else show.status,
        created_at=show.created_at, updated_at=show.updated_at,
    )


@router.delete("/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_show(
    show_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    await db.delete(show)
    await db.flush()
