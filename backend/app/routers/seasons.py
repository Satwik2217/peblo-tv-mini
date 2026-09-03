from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.season import Season
from app.models.show import Show
from app.models.episode import Episode
from app.schemas.season import SeasonCreate, SeasonUpdate, SeasonResponse, SeasonListResponse
from app.auth import require_editor_or_admin
from app.models.user import User

router = APIRouter(prefix="/admin/seasons", tags=["admin-seasons"])


@router.get("", response_model=SeasonListResponse)
async def list_seasons(
    show_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    query = select(Season)
    count_query = select(func.count(Season.id))

    if show_id:
        query = query.where(Season.show_id == show_id)
        count_query = count_query.where(Season.show_id == show_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Season.season_number)
    result = await db.execute(query)
    seasons = result.scalars().all()

    items = []
    for season in seasons:
        episodes_count_result = await db.execute(
            select(func.count(Episode.id)).where(Episode.season_id == season.id)
        )
        episodes_count = episodes_count_result.scalar() or 0
        items.append(SeasonResponse(
            id=season.id,
            show_id=season.show_id,
            season_number=season.season_number,
            title=season.title,
            created_at=season.created_at,
            updated_at=season.updated_at,
            episodes_count=episodes_count,
        ))

    return SeasonListResponse(items=items, total=total)


@router.post("", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
async def create_season(
    season_data: SeasonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    show_result = await db.execute(select(Show).where(Show.id == season_data.show_id))
    if not show_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Show not found")

    existing = await db.execute(
        select(Season).where(Season.show_id == season_data.show_id, Season.season_number == season_data.season_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Season {season_data.season_number} already exists for this show.")

    season = Season(
        show_id=season_data.show_id,
        season_number=season_data.season_number,
        title=season_data.title,
    )
    db.add(season)
    await db.flush()
    await db.refresh(season)
    return SeasonResponse(
        id=season.id, show_id=season.show_id, season_number=season.season_number,
        title=season.title, created_at=season.created_at, updated_at=season.updated_at,
    )


@router.get("/{season_id}", response_model=SeasonResponse)
async def get_season(
    season_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Season).where(Season.id == season_id))
    season = result.scalar_one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    episodes_count_result = await db.execute(
        select(func.count(Episode.id)).where(Episode.season_id == season.id)
    )
    episodes_count = episodes_count_result.scalar() or 0
    return SeasonResponse(
        id=season.id, show_id=season.show_id, season_number=season.season_number,
        title=season.title, created_at=season.created_at, updated_at=season.updated_at,
        episodes_count=episodes_count,
    )


@router.put("/{season_id}", response_model=SeasonResponse)
async def update_season(
    season_id: int,
    season_data: SeasonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Season).where(Season.id == season_id))
    season = result.scalar_one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    if season_data.season_number is not None:
        season.season_number = season_data.season_number
    if season_data.title is not None:
        season.title = season_data.title

    await db.flush()
    await db.refresh(season)
    return SeasonResponse(
        id=season.id, show_id=season.show_id, season_number=season.season_number,
        title=season.title, created_at=season.created_at, updated_at=season.updated_at,
    )


@router.delete("/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season(
    season_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Season).where(Season.id == season_id))
    season = result.scalar_one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    await db.delete(season)
    await db.flush()
