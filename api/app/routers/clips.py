import secrets
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.clip import Clip, ClipTag, Annotation
from app.schemas.clip import ClipCreate, ClipResponse, AnnotationCreate, AnnotationResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/clips", tags=["Clips"])


@router.post("/", response_model=ClipResponse, status_code=201)
async def create_clip(
    request: ClipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clip = Clip(
        match_id=UUID(request.match_id),
        video_id=UUID(request.video_id),
        created_by=current_user.id,
        title=request.title,
        description=request.description,
        start_ms=request.start_ms,
        end_ms=request.end_ms,
        duration_ms=request.end_ms - request.start_ms,
        follow_player_id=UUID(request.follow_player_id) if request.follow_player_id else None,
        follow_ball=request.follow_ball,
        keyframes=request.keyframes,
        ability_labels=request.ability_labels,
        share_token=secrets.token_urlsafe(32),
    )
    db.add(clip)
    await db.flush()

    if request.tags:
        for tag_name in request.tags:
            tag = ClipTag(clip_id=clip.id, tag=tag_name)
            db.add(tag)
        await db.flush()

    await db.refresh(clip)
    return clip


@router.get("/", response_model=list[ClipResponse])
async def list_clips(
    db: AsyncSession = Depends(get_db),
    match_id: str | None = None,
    player_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = select(Clip)
    if match_id:
        query = query.where(Clip.match_id == UUID(match_id))
    if player_id:
        query = query.where(Clip.follow_player_id == UUID(player_id))
    query = query.order_by(Clip.start_ms).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(clip_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Clip).where(Clip.id == UUID(clip_id)))
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.get("/shared/{share_token}", response_model=ClipResponse)
async def get_shared_clip(share_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Clip).where(Clip.share_token == share_token, Clip.is_public == True)
    )
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found or not public")
    return clip


@router.put("/{clip_id}/publish")
async def toggle_publish(
    clip_id: str,
    is_public: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Clip).where(Clip.id == UUID(clip_id)))
    clip = result.scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.is_public = is_public
    await db.flush()
    return {"share_url": f"/clips/shared/{clip.share_token}" if is_public else None}


# Annotations
@router.post("/{clip_id}/annotations", response_model=AnnotationResponse, status_code=201)
async def create_annotation(
    clip_id: str, request: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    annotation = Annotation(
        clip_id=UUID(clip_id),
        created_by=current_user.id,
        annotation_type=request.annotation_type,
        timestamp_ms=request.timestamp_ms,
        duration_ms=request.duration_ms,
        data=request.data,
        color=request.color,
    )
    db.add(annotation)
    await db.flush()
    await db.refresh(annotation)
    return annotation


@router.get("/{clip_id}/annotations", response_model=list[AnnotationResponse])
async def list_annotations(clip_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Annotation).where(Annotation.clip_id == UUID(clip_id))
        .order_by(Annotation.timestamp_ms)
    )
    return result.scalars().all()
