from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.artwork import Artwork
from app.models.episode import Episode
from app.models.show import Show
from app.schemas.artwork import ArtworkResponse
from app.auth import require_editor_or_admin
from app.models.user import User
from app.validation import validate_artwork, detect_mime_type, ALLOWED_MIME_TYPES
from app.storage import get_storage_backend

router = APIRouter(prefix="/admin/artworks", tags=["admin-artworks"])


@router.post("", response_model=ArtworkResponse, status_code=status.HTTP_201_CREATED)
async def upload_artwork(
    artwork_type: str = Form(...),
    episode_id: int = Form(None),
    show_id: int = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    if artwork_type not in ["poster", "banner", "thumbnail"]:
        raise HTTPException(status_code=400, detail="artwork_type must be one of: poster, banner, thumbnail")

    if not episode_id and not show_id:
        raise HTTPException(status_code=400, detail="Either episode_id or show_id must be provided")

    if episode_id:
        result = await db.execute(select(Episode).where(Episode.id == episode_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Episode not found")

    if show_id:
        result = await db.execute(select(Show).where(Show.id == show_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Show not found")

    data = await file.read()

    # Detect actual mime type from file content, not just filename
    mime_type = detect_mime_type(data, file.filename or "")
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {mime_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    validation = validate_artwork(data, artwork_type, file.filename or "")
    if not validation["valid"]:
        error_details = "\n".join(validation["errors"])
        raise HTTPException(status_code=400, detail=error_details)

    storage = get_storage_backend()
    prefix = f"artworks/{artwork_type}"
    key = storage.generate_key(file.filename or "image.jpg", prefix=prefix)
    await storage.save(key, data, mime_type)

    # Remove old artwork of same type for same entity
    if episode_id:
        old_result = await db.execute(
            select(Artwork).where(Artwork.episode_id == episode_id, Artwork.artwork_type == artwork_type)
        )
        for old_artwork in old_result.scalars().all():
            await storage.delete(old_artwork.storage_key)
            await db.delete(old_artwork)

    if show_id:
        old_result = await db.execute(
            select(Artwork).where(Artwork.show_id == show_id, Artwork.artwork_type == artwork_type)
        )
        for old_artwork in old_result.scalars().all():
            await storage.delete(old_artwork.storage_key)
            await db.delete(old_artwork)

    artwork = Artwork(
        episode_id=episode_id,
        show_id=show_id,
        artwork_type=artwork_type,
        storage_key=key,
        original_filename=file.filename,
        mime_type=mime_type,
        file_size=len(data),
        width=validation["width"],
        height=validation["height"],
    )
    db.add(artwork)
    await db.flush()
    await db.refresh(artwork)

    return ArtworkResponse(
        id=artwork.id,
        show_id=artwork.show_id,
        episode_id=artwork.episode_id,
        artwork_type=artwork.artwork_type,
        storage_key=artwork.storage_key,
        original_filename=artwork.original_filename,
        mime_type=artwork.mime_type,
        file_size=artwork.file_size,
        width=artwork.width,
        height=artwork.height,
        created_at=artwork.created_at,
        url=storage.public_url(artwork.storage_key),
    )


@router.delete("/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artwork(
    artwork_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin),
):
    result = await db.execute(select(Artwork).where(Artwork.id == artwork_id))
    artwork = result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    storage = get_storage_backend()
    await storage.delete(artwork.storage_key)
    await db.delete(artwork)
    await db.flush()
