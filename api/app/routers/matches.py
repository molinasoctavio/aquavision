from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.match import Match, MatchEvent, MatchStatus
from app.schemas.match import MatchCreate, MatchResponse, MatchEventCreate, MatchEventResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.post("/", response_model=MatchResponse, status_code=201)
async def create_match(
    request: MatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = Match(
        home_team_id=UUID(request.home_team_id),
        away_team_id=UUID(request.away_team_id),
        tournament_id=UUID(request.tournament_id) if request.tournament_id else None,
        season_id=UUID(request.season_id) if request.season_id else None,
        scheduled_at=request.scheduled_at,
        venue=request.venue,
        pool_length=request.pool_length,
        pool_width=request.pool_width,
        period_duration=request.period_duration,
        shot_clock=request.shot_clock,
        notes=request.notes,
    )
    db.add(match)
    await db.flush()
    await db.refresh(match)
    return match


@router.get("/", response_model=list[MatchResponse])
async def list_matches(
    db: AsyncSession = Depends(get_db),
    team_id: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = select(Match)
    if team_id:
        uid = UUID(team_id)
        query = query.where(or_(Match.home_team_id == uid, Match.away_team_id == uid))
    if status:
        query = query.where(Match.status == MatchStatus(status))
    query = query.order_by(Match.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == UUID(match_id)))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.post("/{match_id}/events", response_model=MatchEventResponse, status_code=201)
async def create_event(
    match_id: str, request: MatchEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = MatchEvent(
        match_id=UUID(match_id),
        event_type=request.event_type,
        period=request.period,
        timestamp_ms=request.timestamp_ms,
        game_clock_seconds=request.game_clock_seconds,
        player_id=UUID(request.player_id) if request.player_id else None,
        secondary_player_id=UUID(request.secondary_player_id) if request.secondary_player_id else None,
        team_id=UUID(request.team_id) if request.team_id else None,
        position_x=request.position_x,
        position_y=request.position_y,
        details=request.details,
        is_auto_detected=False,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.get("/{match_id}/events", response_model=list[MatchEventResponse])
async def list_events(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    event_type: str | None = None,
    period: str | None = None,
):
    query = select(MatchEvent).where(MatchEvent.match_id == UUID(match_id))
    if event_type:
        query = query.where(MatchEvent.event_type == event_type)
    if period:
        query = query.where(MatchEvent.period == period)
    query = query.order_by(MatchEvent.timestamp_ms)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{match_id}/status")
async def update_match_status(
    match_id: str,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Match).where(Match.id == UUID(match_id)))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.status = MatchStatus(new_status)
    await db.flush()
    return {"status": "updated", "new_status": new_status}
