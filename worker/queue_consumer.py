"""
Redis queue consumer — runs all agents in a unified worker process.
Alternative to Celery for simpler deployments.
"""
import asyncio
import json
import signal
import sys
import structlog

from app.config import get_settings
from agents.video_ingestion_agent import VideoIngestionAgent
from agents.video_processing_agent import VideoProcessingAgent
from agents.waterpolo_detection_agent import WaterpoloDetectionAgent
from agents.analytics_engine_agent import AnalyticsEngineAgent
from agents.clip_generation_agent import ClipGenerationAgent
from agents.player_spotlight_agent import PlayerSpotlightAgent
from agents.sharing_export_agent import SharingExportAgent
from agents.db_writer_agent import DBWriterAgent

settings = get_settings()
logger = structlog.get_logger()


async def main():
    agents = [
        VideoIngestionAgent(),
        VideoProcessingAgent(),
        WaterpoloDetectionAgent(),
        AnalyticsEngineAgent(),
        ClipGenerationAgent(),
        PlayerSpotlightAgent(),
        SharingExportAgent(),
        DBWriterAgent(),
    ]

    logger.info("Starting AquaVision worker", agents=[a.name for a in agents])

    tasks = [asyncio.create_task(agent.run()) for agent in agents]

    def shutdown(sig, frame):
        logger.info("Shutting down workers")
        for agent in agents:
            agent.stop()
        for t in tasks:
            t.cancel()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
