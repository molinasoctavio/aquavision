import uuid as uuid_lib
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.video import Video, VideoStatus, VideoSource
from app.schemas.video import VideoResponse, VideoUploadResponse, VideoURLIngest, VideoProcessingStatus
from app.middleware.auth import get_current_user
from app.services.storage import StorageService
from app.services.video_queue import enqueue_video_processing

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post("/upload", response_model=VideoUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    match_id: str = Form(None),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ["mp4", "mov", "avi", "mkv", "webm", "m4v", "flv", "wmv", "ts"]:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    video_id = uuid_lib.uuid4()
    storage_path = f"raw/{video_id}/{file.filename}"

    # Upload to storage
    storage = StorageService()
    await storage.upload_file(file, storage_path, bucket="aquavision-raw")

    video = Video(
        id=video_id,
        title=title,
        description=description,
        match_id=UUID(match_id) if match_id else None,
        uploaded_by=current_user.id,
        source=VideoSource.UPLOAD,
        status=VideoStatus.UPLOADED,
        original_filename=file.filename,
        storage_path=storage_path,
        file_size_bytes=file.size,
    )
    db.add(video)
    await db.flush()

    # Enqueue processing
    await enqueue_video_processing(str(video_id))

    return VideoUploadResponse(
        id=str(video.id), title=video.title,
        status=video.status.value, created_at=video.created_at,
    )


@router.post("/ingest-url", response_model=VideoUploadResponse, status_code=201)
async def ingest_from_url(
    request: VideoURLIngest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video_id = uuid_lib.uuid4()
    source = VideoSource.URL
    if "youtube.com" in request.url or "youtu.be" in request.url:
        source = VideoSource.YOUTUBE

    video = Video(
        id=video_id,
        title=request.title or f"Video from URL",
        match_id=UUID(request.match_id) if request.match_id else None,
        uploaded_by=current_user.id,
        source=source,
        source_url=request.url,
        status=VideoStatus.QUEUED,
    )
    db.add(video)
    await db.flush()

    await enqueue_video_processing(str(video_id))

    return VideoUploadResponse(
        id=str(video.id), title=video.title,
        status=video.status.value, created_at=video.created_at,
    )


@router.get("/", response_model=list[VideoResponse])
async def list_videos(
    db: AsyncSession = Depends(get_db),
    match_id: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = select(Video)
    if match_id:
        query = query.where(Video.match_id == UUID(match_id))
    if status:
        query = query.where(Video.status == VideoStatus(status))
    query = query.order_by(Video.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == UUID(video_id)))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/status", response_model=VideoProcessingStatus)
async def get_processing_status(video_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == UUID(video_id)))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoProcessingStatus(
        video_id=str(video.id),
        status=video.status.value,
        progress=video.processing_progress,
        current_step=video.processing_metadata.get("current_step") if video.processing_metadata else None,
        error=video.processing_error,
    )


@router.get("/{video_id}/stream-url")
async def get_stream_url(video_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == UUID(video_id)))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != VideoStatus.READY:
        raise HTTPException(status_code=400, detail="Video not yet processed")

    storage = StorageService()
    url = await storage.get_presigned_url(video.hls_path or video.storage_path)
    return {"stream_url": url, "hls_path": video.hls_path}
