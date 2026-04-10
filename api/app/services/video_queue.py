import redis.asyncio as aioredis
import json
from app.config import get_settings

settings = get_settings()


async def enqueue_video_processing(video_id: str, priority: int = 0):
    """Add a video to the processing queue."""
    r = aioredis.from_url(settings.REDIS_URL)
    task = json.dumps({
        "video_id": video_id,
        "priority": priority,
        "task_type": "full_pipeline",
    })
    await r.lpush("aquavision:video_queue", task)
    await r.close()


async def enqueue_clip_export(clip_id: str, video_id: str, start_ms: int, end_ms: int, quality: str = "1080p"):
    """Add a clip export task to the queue."""
    r = aioredis.from_url(settings.REDIS_URL)
    task = json.dumps({
        "clip_id": clip_id,
        "video_id": video_id,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "quality": quality,
        "task_type": "clip_export",
    })
    await r.lpush("aquavision:clip_queue", task)
    await r.close()


async def enqueue_analysis(video_id: str, match_id: str):
    """Add an AI analysis task to the queue."""
    r = aioredis.from_url(settings.REDIS_URL)
    task = json.dumps({
        "video_id": video_id,
        "match_id": match_id,
        "task_type": "ai_analysis",
    })
    await r.lpush("aquavision:analysis_queue", task)
    await r.close()


async def get_queue_status() -> dict:
    """Get processing queue status."""
    r = aioredis.from_url(settings.REDIS_URL)
    video_queue_len = await r.llen("aquavision:video_queue")
    clip_queue_len = await r.llen("aquavision:clip_queue")
    analysis_queue_len = await r.llen("aquavision:analysis_queue")
    await r.close()
    return {
        "video_queue": video_queue_len,
        "clip_queue": clip_queue_len,
        "analysis_queue": analysis_queue_len,
    }
