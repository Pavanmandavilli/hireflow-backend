from __future__ import annotations

import asyncio
from app.logging.logger import get_logger

logger = get_logger("task-worker")

_task: asyncio.Task | None = None
_running = False


async def _worker_loop() -> None:
    logger.info("Background worker loop started")
    while _running:
        try:
            await _process_pending_tasks()
        except Exception as exc:
            logger.error(f"Worker error: {exc}")
        await asyncio.sleep(5)
    logger.info("Background worker loop stopped")


async def _process_pending_tasks() -> None:
    """Replace this stub with your actual background task logic."""
    logger.debug("Worker tick — processing pending tasks")


async def start_worker() -> None:
    global _task, _running
    _running = True
    _task = asyncio.create_task(_worker_loop())


async def stop_worker() -> None:
    global _task, _running
    _running = False
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
