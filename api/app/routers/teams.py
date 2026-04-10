from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.team import Team, TeamMembership, TeamMemberRole
from app.models.player import Player
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate
from app.schemas.player import PlayerCreate, PlayerResponse, PlayerUpdate
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("/", response_model=TeamResponse, status_code=201)
async def create_team(
    request: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = Team(**request.model_dump())
    db.add(team)
    await db.flush()

    # Add creator as owner
    membership = TeamMembership(
        user_id=current_user.id, team_id=team.id, role=TeamMemberRole.OWNER
    )
    db.add(membership)
    await db.flush()
    await db.refresh(team)
    return team


@router.get("/", response_model=list[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    # Get teams user belongs to
    result = await db.execute(
        select(Team)
        .join(TeamMembership, TeamMembership.team_id == Team.id)
        .where(TeamMembership.user_id == current_user.id)
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == UUID(team_id)))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str, request: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).where(Team.id == UUID(team_id)))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(team, field, value)

    await db.flush()
    await db.refresh(team)
    return team


# Player management within teams
@router.post("/{team_id}/players", response_model=PlayerResponse, status_code=201)
async def add_player(
    team_id: str, request: PlayerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    player = Player(
        team_id=UUID(team_id),
        first_name=request.first_name,
        last_name=request.last_name,
        cap_number=request.cap_number,
        position=request.position,
        date_of_birth=request.date_of_birth,
        height_cm=request.height_cm,
        weight_kg=request.weight_kg,
        dominant_hand=request.dominant_hand,
        nationality=request.nationality,
        photo_url=request.photo_url,
    )
    db.add(player)
    await db.flush()
    await db.refresh(player)
    return player


@router.get("/{team_id}/players", response_model=list[PlayerResponse])
async def list_team_players(
    team_id: str, db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Player).where(Player.team_id == UUID(team_id), Player.is_active == True)
        .order_by(Player.cap_number)
    )
    return result.scalars().all()
