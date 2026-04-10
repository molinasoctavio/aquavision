"""Base Agent class for all AquaVision agents."""
import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Optional
import structlog
import redis

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all AquaVision agents."""

    def __init__(self, name: str):
        self.name = name
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.logger = logger.bind(agent=name)
        self._running = False

    @abstractmethod
    async def process(self, task: dict) -> dict:
        """Process a single task. Must be implemented by subclasses."""
        pass

    @property
    def queue_name(self) -> str:
        return f"aquavision:agent:{self.name}"

    @property
    def status_key(self) -> str:
        return f"aquavision:agent_status:{self.name}"

    def publish_status(self, video_id: str, status: str, progress: float = 0.0, details: dict = None):
        """Publish processing status update."""
        msg = json.dumps({
            "agent": self.name,
            "video_id": video_id,
            "status": status,
            "progress": progress,
            "details": details or {},
            "timestamp": time.time(),
        })
        self.redis.publish(f"aquavision:status:{video_id}", msg)
        self.redis.hset(self.status_key, video_id, msg)

    def enqueue(self, task: dict):
        """Add task to this agent's queue."""
        self.redis.lpush(self.queue_name, json.dumps(task))

    def enqueue_next(self, next_agent: str, task: dict):
        """Forward task to another agent's queue."""
        queue = f"aquavision:agent:{next_agent}"
        self.redis.lpush(queue, json.dumps(task))
        self.logger.info("Forwarded task", next_agent=next_agent, task_type=task.get("task_type"))

    async def run(self):
        """Main agent loop — consume tasks from queue."""
        self._running = True
        self.logger.info("Agent started", queue=self.queue_name)

        while self._running:
            try:
                # Blocking pop with 5s timeout
                result = self.redis.brpop(self.queue_name, timeout=5)
                if result is None:
                    continue

                _, raw_task = result
                task = json.loads(raw_task)
                self.logger.info("Processing task", task_type=task.get("task_type"))

                start = time.time()
                output = await self.process(task)
                elapsed = time.time() - start

                self.logger.info(
                    "Task completed",
                    task_type=task.get("task_type"),
                    elapsed_seconds=round(elapsed, 2),
                )

            except Exception as e:
                self.logger.error("Task failed", error=str(e), exc_info=True)
                if 'task' in locals():
                    self.publish_status(
                        task.get("video_id", "unknown"),
                        "error",
                        details={"error": str(e)},
                    )

    def stop(self):
        self._running = False
        self.logger.info("Agent stopping")
