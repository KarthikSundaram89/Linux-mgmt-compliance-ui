"""
Scheduler Manager
=================

Manages APScheduler for automated inventory collection.
Handles daily collection, retry logic for failed servers,
and manual collection triggers.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.settings.config import Settings

logger = logging.getLogger("scheduler")


class SchedulerState(str, Enum):
    """Scheduler operational states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class SchedulerManager:
    """
    Manages scheduled inventory collection tasks.
    
    Features:
    - Daily scheduled collection of all active servers
    - Automatic retry of failed collections every hour
    - Manual trigger support (collect now, retry now)
    - Pause/resume capabilities
    - Independent retry logic per server
    
    The scheduler does not perform collection itself;
    it delegates to the CollectionService.
    """
    
    JOB_ID_DAILY = "daily_collection"
    JOB_ID_RETRY = "retry_failed_collections"
    
    def __init__(self, settings: Settings):
        self._settings = settings
        self._scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
        )
        self._state = SchedulerState.STOPPED
        self._last_collection_time: Optional[datetime] = None
        self._last_retry_time: Optional[datetime] = None
    
    @property
    def state(self) -> SchedulerState:
        """Current scheduler state."""
        return self._state
    
    @property
    def last_collection_time(self) -> Optional[datetime]:
        """Timestamp of last daily collection run."""
        return self._last_collection_time
    
    @property
    def last_retry_time(self) -> Optional[datetime]:
        """Timestamp of last retry run."""
        return self._last_retry_time
    
    async def start(self) -> None:
        """
        Start the scheduler with configured jobs.
        
        Creates two recurring jobs:
        1. Daily collection at the configured hour
        2. Retry of failed collections every configured interval
        """
        if not self._settings.scheduler_enabled:
            logger.info("Scheduler disabled in configuration")
            return
        
        # Daily collection job
        self._scheduler.add_job(
            self._run_daily_collection,
            trigger=CronTrigger(
                hour=self._settings.scheduler_collection_hour,
                minute=self._settings.scheduler_collection_minute,
            ),
            id=self.JOB_ID_DAILY,
            name="Daily Server Collection",
            replace_existing=True,
        )
        
        # Retry failed collections job
        self._scheduler.add_job(
            self._run_retry_failed,
            trigger=IntervalTrigger(
                minutes=self._settings.scheduler_retry_interval_minutes
            ),
            id=self.JOB_ID_RETRY,
            name="Retry Failed Collections",
            replace_existing=True,
        )
        
        self._scheduler.start()
        self._state = SchedulerState.RUNNING
        
        logger.info(
            "Scheduler started",
            extra={
                "daily_hour": self._settings.scheduler_collection_hour,
                "retry_interval_min": self._settings.scheduler_retry_interval_minutes,
            },
        )
    
    async def shutdown(self) -> None:
        """Gracefully shut down the scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
        self._state = SchedulerState.STOPPED
        logger.info("Scheduler shut down")
    
    async def pause(self) -> None:
        """Pause all scheduled jobs."""
        self._scheduler.pause()
        self._state = SchedulerState.PAUSED
        logger.info("Scheduler paused")
    
    async def resume(self) -> None:
        """Resume all scheduled jobs."""
        self._scheduler.resume()
        self._state = SchedulerState.RUNNING
        logger.info("Scheduler resumed")
    
    async def trigger_collection_now(self) -> str:
        """
        Manually trigger a full collection immediately.
        
        Returns:
            str: Job execution ID for tracking.
        """
        job = self._scheduler.get_job(self.JOB_ID_DAILY)
        if job:
            job.modify(next_run_time=datetime.now(timezone.utc))
            logger.info("Manual collection triggered")
            return self.JOB_ID_DAILY
        
        # If job doesn't exist, add one-shot job
        self._scheduler.add_job(
            self._run_daily_collection,
            id="manual_collection",
            name="Manual Collection",
            replace_existing=True,
        )
        return "manual_collection"
    
    async def trigger_retry_now(self) -> str:
        """
        Manually trigger retry of failed collections.
        
        Returns:
            str: Job execution ID for tracking.
        """
        job = self._scheduler.get_job(self.JOB_ID_RETRY)
        if job:
            job.modify(next_run_time=datetime.now(timezone.utc))
            logger.info("Manual retry triggered")
            return self.JOB_ID_RETRY
        return ""
    
    async def get_status(self) -> dict:
        """
        Get comprehensive scheduler status.
        
        Returns:
            dict: Scheduler state, job details, and timing info.
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time),
                "trigger": str(job.trigger),
            })
        
        return {
            "state": self._state.value,
            "jobs": jobs,
            "last_collection_time": (
                self._last_collection_time.isoformat()
                if self._last_collection_time
                else None
            ),
            "last_retry_time": (
                self._last_retry_time.isoformat()
                if self._last_retry_time
                else None
            ),
            "max_concurrent": (
                self._settings.scheduler_max_concurrent_collections
            ),
        }
    
    async def _run_daily_collection(self) -> None:
        """
        Execute the daily collection of all active servers.
        
        This method is called by the scheduler. It delegates
        actual collection to the CollectionService.
        """
        self._last_collection_time = datetime.now(timezone.utc)
        logger.info("Starting daily collection run")
        
        # Import here to avoid circular imports
        from backend.services.collection_service import (
            CollectionService,
        )
        
        # The actual collection is orchestrated by CollectionService
        # This will be fully wired in Phase 2
        try:
            service = CollectionService()
            await service.collect_all_servers()
        except Exception as e:
            logger.error(
                f"Daily collection failed: {e}",
                exc_info=True,
            )
    
    async def _run_retry_failed(self) -> None:
        """
        Retry collection for servers that previously failed.
        
        Only retries servers marked as failed.
        Each server's retry is independent.
        """
        self._last_retry_time = datetime.now(timezone.utc)
        logger.info("Starting retry of failed collections")
        
        from backend.services.collection_service import (
            CollectionService,
        )
        
        try:
            service = CollectionService()
            await service.retry_failed_servers()
        except Exception as e:
            logger.error(
                f"Retry failed collections error: {e}",
                exc_info=True,
            )
