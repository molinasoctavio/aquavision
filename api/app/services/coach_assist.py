from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import anthropic
import json

from app.config import get_settings
from app.models.match import Match, MatchEvent
from app.models.analytics import MatchAnalytics, PlayerMatchStats
from app.models.player import Player
from app.models.team import Team
from app.schemas.analytics import CoachAssistResponse

settings = get_settings()


class CoachAssistService:
    """AI-powered coaching assistant using Claude API."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def _gather_match_context(self, match_id: str) -> dict:
        """Gather all relevant match data for the AI context."""
        mid = UUID(match_id)

        # Get match
        result = await self.db.execute(select(Match).where(Match.id == mid))
        match = result.scalar_one_or_none()
        if not match:
            return {}

        # Get teams
        home_result = await self.db.execute(select(Team).where(Team.id == match.home_team_id))
        home_team = home_result.scalar_one_or_none()
        away_result = await self.db.execute(select(Team).where(Team.id == match.away_team_id))
        away_team = away_result.scalar_one_or_none()

        # Get events
        events_result = await self.db.execute(
            select(MatchEvent).where(MatchEvent.match_id == mid)
            .order_by(MatchEvent.timestamp_ms)
        )
        events = events_result.scalars().all()

        # Get analytics
        analytics_result = await self.db.execute(
            select(MatchAnalytics).where(MatchAnalytics.match_id == mid)
        )
        analytics = analytics_result.scalar_one_or_none()

        # Get player stats
        pstats_result = await self.db.execute(
            select(PlayerMatchStats).where(PlayerMatchStats.match_id == mid)
        )
        player_stats = pstats_result.scalars().all()

        # Get player names
        player_ids = set()
        for e in events:
            if e.player_id:
                player_ids.add(e.player_id)
        for ps in player_stats:
            player_ids.add(ps.player_id)

        players = {}
        if player_ids:
            p_result = await self.db.execute(
                select(Player).where(Player.id.in_(player_ids))
            )
            for p in p_result.scalars().all():
                players[str(p.id)] = f"#{p.cap_number} {p.first_name} {p.last_name}"

        return {
            "match": {
                "home_team": home_team.name if home_team else "Home",
                "away_team": away_team.name if away_team else "Away",
                "home_score": match.home_score,
                "away_score": match.away_score,
                "venue": match.venue,
                "pool_length": match.pool_length,
                "pool_width": match.pool_width,
                "period_duration": match.period_duration,
            },
            "events": [
                {
                    "type": e.event_type.value if hasattr(e.event_type, 'value') else e.event_type,
                    "period": e.period.value if hasattr(e.period, 'value') else e.period,
                    "timestamp_ms": e.timestamp_ms,
                    "player": players.get(str(e.player_id), "Unknown") if e.player_id else None,
                    "position": {"x": e.position_x, "y": e.position_y} if e.position_x else None,
                }
                for e in events
            ],
            "analytics": {
                "home_possession_pct": analytics.home_possession_pct if analytics else None,
                "away_possession_pct": analytics.away_possession_pct if analytics else None,
                "home_shots": analytics.home_shots if analytics else 0,
                "away_shots": analytics.away_shots if analytics else 0,
                "home_power_play_attempts": analytics.home_power_play_attempts if analytics else 0,
                "home_power_play_goals": analytics.home_power_play_goals if analytics else 0,
                "away_power_play_attempts": analytics.away_power_play_attempts if analytics else 0,
                "away_power_play_goals": analytics.away_power_play_goals if analytics else 0,
            } if analytics else {},
            "player_stats": [
                {
                    "player": players.get(str(ps.player_id), "Unknown"),
                    "goals": ps.goals,
                    "assists": ps.assists,
                    "shots": ps.shots,
                    "saves": ps.saves,
                    "exclusions_drawn": ps.exclusions_drawn,
                    "exclusions_committed": ps.exclusions_committed,
                    "steals": ps.steals,
                }
                for ps in player_stats
            ],
            "players": players,
        }

    async def answer_question(self, match_id: str, question: str) -> CoachAssistResponse:
        context = await self._gather_match_context(match_id)

        system_prompt = """You are AquaVision CoachAssist, an expert water polo tactical analyst AI.
You have deep knowledge of water polo rules (FINA/World Aquatics), tactics, and strategy.

Key water polo concepts you understand:
- Pool dimensions: typically 30m x 20m
- 4 periods of 8 minutes each
- 30-second shot clock
- Exclusions (major fouls) create 6v5 power play situations for 20 seconds
- 5-meter penalty shots
- Positions: goalkeeper, center forward (boya/pivot), center back, wing, flat, point
- Tactical formations: 3-3, 4-2, arc offense
- Counterattack vs. set offense
- Man-up/man-down (power play) tactics
- Pressing defense vs. zone defense

When answering questions:
1. Be specific and data-driven, referencing actual match statistics
2. Suggest tactical adjustments based on the data
3. Identify key moments and turning points
4. Compare performance across periods
5. Provide actionable coaching insights
6. Reference specific players by cap number when relevant

Respond in the same language as the question (Spanish or English)."""

        user_message = f"""Match Context:
{json.dumps(context, indent=2, default=str)}

Coach's Question: {question}"""

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        answer = response.content[0].text

        # Generate follow-up suggestions
        follow_ups = await self._generate_follow_ups(context, question, answer)

        return CoachAssistResponse(
            match_id=match_id,
            question=question,
            answer=answer,
            suggested_follow_ups=follow_ups,
        )

    async def _generate_follow_ups(self, context: dict, question: str, answer: str) -> list[str]:
        """Generate suggested follow-up questions."""
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"""Based on this water polo match analysis conversation:
Question: {question}
Answer: {answer}

Generate 3 short follow-up questions a coach might ask. Return only the questions, one per line.""",
            }],
        )
        lines = response.content[0].text.strip().split("\n")
        return [line.strip().lstrip("0123456789.-) ") for line in lines if line.strip()][:3]

    async def generate_post_match_summary(self, match_id: str) -> str:
        """Generate automatic post-match summary."""
        context = await self._gather_match_context(match_id)

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=3000,
            system="""You are AquaVision CoachAssist. Generate a comprehensive post-match analysis report for a water polo match.
Include: match overview, key statistics, tactical analysis, player highlights, areas for improvement, and recommendations for next match.
Use the coach's language (detect from team names or default to English).""",
            messages=[{
                "role": "user",
                "content": f"Generate a post-match report:\n{json.dumps(context, indent=2, default=str)}",
            }],
        )
        return response.content[0].text
