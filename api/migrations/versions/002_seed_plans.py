"""Seed subscription plans

Revision ID: 002
"""
from alembic import op
import uuid, sqlalchemy as sa

revision = "002"
down_revision = "001"


def upgrade():
    plans = [
        {
            "id": str(uuid.uuid4()), "tier": "starter", "name": "Starter",
            "description": "Grabación básica sin descarga",
            "price_monthly": 9.99, "price_semiannual": 8.99,
            "price_annual": 7.99, "price_biannual": 6.99,
            "max_videos_per_month": 5, "max_storage_gb": 50,
            "can_download": False, "has_drawing_tools": False,
            "has_analytics": False, "has_coach_assist": False,
            "has_player_spotlight": False, "has_live_streaming": False,
            "max_cameras": 1, "has_multi_camera": False,
            "has_export_social": False, "has_api_access": False,
        },
        {
            "id": str(uuid.uuid4()), "tier": "standard", "name": "Standard",
            "description": "Editor completo + descarga",
            "price_monthly": 24.99, "price_semiannual": 21.99,
            "price_annual": 19.99, "price_biannual": 16.99,
            "max_videos_per_month": 20, "max_storage_gb": 200,
            "can_download": True, "has_drawing_tools": True,
            "has_analytics": False, "has_coach_assist": False,
            "has_player_spotlight": False, "has_live_streaming": False,
            "max_cameras": 1, "has_multi_camera": False,
            "has_export_social": True, "has_api_access": False,
        },
        {
            "id": str(uuid.uuid4()), "tier": "analytics", "name": "Analytics",
            "description": "AquaStats + CoachAssist IA",
            "price_monthly": 49.99, "price_semiannual": 44.99,
            "price_annual": 39.99, "price_biannual": 34.99,
            "max_videos_per_month": 50, "max_storage_gb": 500,
            "can_download": True, "has_drawing_tools": True,
            "has_analytics": True, "has_coach_assist": True,
            "has_player_spotlight": False, "has_live_streaming": False,
            "max_cameras": 2, "has_multi_camera": True,
            "has_export_social": True, "has_api_access": False,
        },
        {
            "id": str(uuid.uuid4()), "tier": "elite", "name": "Elite",
            "description": "Todo incluido: Player Spotlight + Live + Multi-cámara",
            "price_monthly": 99.99, "price_semiannual": 89.99,
            "price_annual": 79.99, "price_biannual": 69.99,
            "max_videos_per_month": 999, "max_storage_gb": 2000,
            "can_download": True, "has_drawing_tools": True,
            "has_analytics": True, "has_coach_assist": True,
            "has_player_spotlight": True, "has_live_streaming": True,
            "max_cameras": 4, "has_multi_camera": True,
            "has_export_social": True, "has_api_access": True,
        },
    ]

    conn = op.get_bind()
    for plan in plans:
        conn.execute(
            sa.text("""
                INSERT INTO subscription_plans
                (id, tier, name, description, price_monthly, price_semiannual,
                 price_annual, price_biannual, max_videos_per_month, max_storage_gb,
                 can_download, has_drawing_tools, has_analytics, has_coach_assist,
                 has_player_spotlight, has_live_streaming, max_cameras,
                 has_multi_camera, has_export_social, has_api_access)
                VALUES (:id, :tier, :name, :description, :price_monthly,
                        :price_semiannual, :price_annual, :price_biannual,
                        :max_videos_per_month, :max_storage_gb, :can_download,
                        :has_drawing_tools, :has_analytics, :has_coach_assist,
                        :has_player_spotlight, :has_live_streaming, :max_cameras,
                        :has_multi_camera, :has_export_social, :has_api_access)
                ON CONFLICT DO NOTHING
            """),
            plan,
        )


def downgrade():
    op.get_bind().execute(sa.text("DELETE FROM subscription_plans"))
