from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.analytics import MatchAnalytics, PlayerMatchStats, ShotRecord
from app.schemas.analytics import (
    MatchAnalyticsResponse, PlayerMatchStatsResponse,
    ShotMapResponse, CoachAssistQuery, CoachAssistResponse,
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/matches/{match_id}", response_model=MatchAnalyticsResponse)
async def get_match_analytics(match_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MatchAnalytics).where(MatchAnalytics.match_id == UUID(match_id))
    )
    analytics = result.scalar_one_or_none()
    if not analytics:
        raise HTTPException(status_code=404, detail="Analytics not found for this match")
    return analytics


@router.get("/matches/{match_id}/players", response_model=list[PlayerMatchStatsResponse])
async def get_player_match_stats(match_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlayerMatchStats).where(PlayerMatchStats.match_id == UUID(match_id))
    )
    return result.scalars().all()


@router.get("/matches/{match_id}/players/{player_id}", response_model=PlayerMatchStatsResponse)
async def get_player_stats_for_match(
    match_id: str, player_id: str, db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlayerMatchStats).where(
            PlayerMatchStats.match_id == UUID(match_id),
            PlayerMatchStats.player_id == UUID(player_id),
        )
    )
    stats = result.scalar_one_or_none()
    if not stats:
        raise HTTPException(status_code=404, detail="Player stats not found")
    return stats


@router.get("/matches/{match_id}/shots", response_model=ShotMapResponse)
async def get_shot_map(
    match_id: str,
    player_id: str | None = None,
    period: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ShotRecord).where(ShotRecord.match_id == UUID(match_id))
    if player_id:
        query = query.where(ShotRecord.player_id == UUID(player_id))
    if period:
        query = query.where(ShotRecord.period == period)

    result = await db.execute(query)
    shots = result.scalars().all()

    shot_dicts = []
    goals = saves = misses = blocks = 0
    for s in shots:
        shot_dicts.append({
            "id": str(s.id),
            "player_id": str(s.player_id) if s.player_id else None,
            "period": s.period,
            "timestamp_ms": s.timestamp_ms,
            "shot_x": s.shot_x,
            "shot_y": s.shot_y,
            "target_x": s.target_x,
            "target_y": s.target_y,
            "outcome": s.outcome,
            "shot_type": s.shot_type,
            "is_power_play": s.is_power_play,
            "is_penalty": s.is_penalty,
        })
        if s.outcome == "goal":
            goals += 1
        elif s.outcome == "saved":
            saves += 1
        elif s.outcome == "missed":
            misses += 1
        elif s.outcome == "blocked":
            blocks += 1

    return ShotMapResponse(
        match_id=match_id, shots=shot_dicts,
        total_shots=len(shots), goals=goals,
        saves=saves, misses=misses, blocks=blocks,
    )


@router.post("/coach-assist", response_model=CoachAssistResponse)
async def coach_assist_query(
    request: CoachAssistQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Import here to avoid circular imports
    from app.services.coach_assist import CoachAssistService

    service = CoachAssistService(db)
    response = await service.answer_question(request.match_id, request.question)
    return response
