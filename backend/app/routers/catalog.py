from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.publish_run import PublishRun
from app.models.user import User
from app.auth import require_admin, require_editor_or_admin
from app.publishing import run_publish
from app.schemas.publish_run import PublishRunResponse, PublishRunListResponse
from app.routers.validation_report import get_validation_report

router = APIRouter(prefix="/admin/catalog", tags=["admin-catalog"])


@router.post("/publish", response_model=PublishRunResponse)
async def publish_catalog(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Check validation first
    report = await get_validation_report(db=db, current_user=current_user)
    if report["total_blocking"] > 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot publish: {report['total_blocking']} blocking issue(s) found. Fix them first.",
        )

    publish_run = await run_publish(current_user, db)
    return PublishRunResponse(
        id=publish_run.id,
        initiated_by=publish_run.initiated_by,
        started_at=publish_run.started_at,
        completed_at=publish_run.completed_at,
        status=publish_run.status.value if hasattr(publish_run.status, 'value') else publish_run.status,
        shows_count=publish_run.shows_count,
        episodes_count=publish_run.episodes_count,
        catalogue_version=publish_run.catalogue_version,
        errors=publish_run.errors,
    )


@router.get("/runs", response_model=PublishRunListResponse)
async def list_publish_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(PublishRun).order_by(PublishRun.started_at.desc()))
    runs = result.scalars().all()
    items = []
    for run in runs:
        items.append(PublishRunResponse(
            id=run.id,
            initiated_by=run.initiated_by,
            started_at=run.started_at,
            completed_at=run.completed_at,
            status=run.status.value if hasattr(run.status, 'value') else run.status,
            shows_count=run.shows_count,
            episodes_count=run.episodes_count,
            catalogue_version=run.catalogue_version,
            errors=run.errors,
        ))
    return PublishRunListResponse(items=items, total=len(items))
