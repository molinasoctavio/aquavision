from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.match import Match, MatchStatus
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/livestream", tags=["Live Streaming"])


class StreamConfig(BaseModel):
    match_id: str
    platforms: list[str] = []  # youtube, facebook, twitch
    youtube_key: str | None = None
    facebook_key: str | None = None
    twitch_key: str | None = None
    overlay_enabled: bool = True
    overlay_config: dict | None = None


class StreamStatus(BaseModel):
    match_id: str
    is_live: bool
    stream_key: str | None = None
    rtmp_url: str | None = None
    webrtc_url: str | None = None
    viewers: int = 0
    uptime_seconds: int = 0
    platforms: list[str] = []


# Active streams registry
active_streams: dict[str, dict] = {}


@router.post("/start", response_model=StreamStatus)
async def start_stream(
    config: StreamConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Match).where(Match.id == UUID(config.match_id)))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    import secrets
    stream_key = secrets.token_urlsafe(16)

    active_streams[config.match_id] = {
        "stream_key": stream_key,
        "platforms": config.platforms,
        "overlay_config": config.overlay_config,
        "is_live": True,
    }

    match.status = MatchStatus.LIVE
    await db.flush()

    from app.config import get_settings
    settings = get_settings()

    return StreamStatus(
        match_id=config.match_id,
        is_live=True,
        stream_key=stream_key,
        rtmp_url=f"{settings.RTMP_SERVER_URL}/live/{stream_key}",
        webrtc_url=f"/api/v1/livestream/webrtc/{config.match_id}",
        platforms=config.platforms,
    )


@router.post("/stop/{match_id}")
async def stop_stream(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if match_id in active_streams:
        del active_streams[match_id]

    result = await db.execute(select(Match).where(Match.id == UUID(match_id)))
    match = result.scalar_one_or_none()
    if match:
        match.status = MatchStatus.RECORDING
        await db.flush()

    return {"status": "stopped"}


@router.get("/status/{match_id}", response_model=StreamStatus)
async def get_stream_status(match_id: str):
    stream = active_streams.get(match_id)
    if not stream:
        return StreamStatus(match_id=match_id, is_live=False)

    return StreamStatus(
        match_id=match_id,
        is_live=stream["is_live"],
        platforms=stream.get("platforms", []),
    )


@router.post("/bookmark/{match_id}")
async def add_live_bookmark(
    match_id: str,
    label: str = "Bookmark",
    current_user: User = Depends(get_current_user),
):
    """Add a real-time bookmark during live streaming (mobile sideline use)."""
    if match_id not in active_streams:
        raise HTTPException(status_code=400, detail="No active stream for this match")

    import time
    bookmark = {
        "label": label,
        "timestamp": time.time(),
        "user_id": str(current_user.id),
    }

    if "bookmarks" not in active_streams[match_id]:
        active_streams[match_id]["bookmarks"] = []
    active_streams[match_id]["bookmarks"].append(bookmark)

    return {"status": "bookmarked", "bookmark": bookmark}


@router.websocket("/ws/{match_id}")
async def stream_websocket(websocket: WebSocket, match_id: str):
    """WebSocket for real-time match updates during live streaming."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "bookmark":
                if match_id in active_streams:
                    if "bookmarks" not in active_streams[match_id]:
                        active_streams[match_id]["bookmarks"] = []
                    active_streams[match_id]["bookmarks"].append(data)
                await websocket.send_json({"status": "ok", "action": "bookmark"})

            elif action == "event":
                await websocket.send_json({"status": "ok", "action": "event_recorded"})

            elif action == "ping":
                await websocket.send_json({"status": "pong"})

    except WebSocketDisconnect:
        pass
