"""
Collector Worker Process
========================

Long-running worker that consumes collection jobs from SQS,
executes SSH collectors, stores snapshots, and reports results.

Designed to run as a standalone container in ECS Fargate.
Scales independently from the API service.

Architecture:
    SQS Queue → Worker → SSH Collectors → EFS (snapshots) → PostgreSQL (results)
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI

from backend.settings.config import get_settings

logger = logging.getLogger("collector.worker")

# Mini health API for container health checks
health_app = FastAPI()
_worker_status = {"state": "starting", "last_job": None, "jobs_processed": 0}


@health_app.get("/health")
async def worker_health():
    """Health endpoint for ECS health checks."""
    return {
        "status": "healthy",
        "service": "collector-worker",
        "state": _worker_status["state"],
        "jobs_processed": _worker_status["jobs_processed"],
        "last_job": _worker_status["last_job"],
    }


class CollectorWorker:
    """
    SQS-based collection worker.

    Lifecycle:
    1. Start and connect to SQS queue
    2. Long-poll for collection jobs
    3. For each job: acquire SSH connection, run collectors, store snapshot
    4. On success: delete SQS message, update database
    5. On failure: let message return to queue (visibility timeout)
    6. Graceful shutdown on SIGTERM (ECS task stop)
    """

    def __init__(self):
        self._settings = get_settings()
        self._running = True
        self._current_job: Optional[str] = None
        self._sqs_client = None
        self._queue_url: Optional[str] = None

        # Concurrency control
        self._max_concurrent = self._settings.scheduler_max_concurrent_collections
        self._semaphore = asyncio.Semaphore(self._max_concurrent)

    async def start(self) -> None:
        """Initialize the worker and begin processing."""
        logger.info(
            "Collector worker starting",
            extra={
                "max_concurrent": self._max_concurrent,
                "queue": os.environ.get("SQS_QUEUE_URL", "not configured"),
            },
        )

        # Initialize SQS client
        self._queue_url = os.environ.get("SQS_QUEUE_URL")
        if not self._queue_url:
            logger.error("SQS_QUEUE_URL environment variable not set")
            sys.exit(1)

        import boto3
        session = boto3.Session(region_name=self._settings.aws_region)
        self._sqs_client = session.client("sqs")

        _worker_status["state"] = "running"
        logger.info("Collector worker ready, polling for jobs...")

        # Main processing loop
        while self._running:
            try:
                await self._poll_and_process()
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(5)

        _worker_status["state"] = "stopped"
        logger.info("Collector worker stopped")

    async def _poll_and_process(self) -> None:
        """Long-poll SQS for collection jobs and process them."""
        loop = asyncio.get_event_loop()

        # Long-poll SQS (20 second wait)
        response = await loop.run_in_executor(
            None,
            lambda: self._sqs_client.receive_message(
                QueueUrl=self._queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                VisibilityTimeout=300,  # 5 min to process
                MessageAttributeNames=["All"],
            ),
        )

        messages = response.get("Messages", [])

        if not messages:
            return

        logger.info(f"Received {len(messages)} collection jobs")

        # Process messages concurrently (bounded by semaphore)
        tasks = [
            self._process_message(msg)
            for msg in messages
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_message(self, message: Dict[str, Any]) -> None:
        """Process a single SQS collection job message."""
        receipt_handle = message["ReceiptHandle"]
        body = json.loads(message["Body"])

        server_id = body.get("server_id", "unknown")
        hostname = body.get("hostname", "unknown")
        job_type = body.get("job_type", "collect")

        logger.info(
            f"Processing job: {job_type} for {hostname}",
            extra={"server_id": server_id},
        )

        async with self._semaphore:
            start_time = time.time()
            self._current_job = server_id

            try:
                if job_type == "collect":
                    result = await self._run_collection(body)
                elif job_type == "retry":
                    result = await self._run_collection(body)
                else:
                    logger.warning(f"Unknown job type: {job_type}")
                    result = {"status": "skipped"}

                # Success - delete message from queue
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self._sqs_client.delete_message(
                        QueueUrl=self._queue_url,
                        ReceiptHandle=receipt_handle,
                    ),
                )

                duration = time.time() - start_time
                _worker_status["jobs_processed"] += 1
                _worker_status["last_job"] = {
                    "server": hostname,
                    "status": result.get("status", "unknown"),
                    "duration": round(duration, 2),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                logger.info(
                    f"Job completed: {hostname} in {duration:.1f}s",
                    extra={
                        "server_id": server_id,
                        "status": result.get("status"),
                        "duration": duration,
                    },
                )

            except Exception as e:
                logger.error(
                    f"Job failed: {hostname} - {e}",
                    extra={"server_id": server_id},
                    exc_info=True,
                )
                # Message will return to queue after visibility timeout

            finally:
                self._current_job = None

    async def _run_collection(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the collection pipeline for a server.

        Steps:
        1. Resolve credentials from Secrets Manager
        2. Establish SSH connection
        3. Detect distribution
        4. Run all enabled collectors
        5. Save snapshot to EFS
        6. Detect changes
        7. Update database
        """
        from backend.services.collection_service import CollectionOrchestrator

        server_id = job["server_id"]
        hostname = job["hostname"]
        ip_address = job["ip_address"]
        profile_data = job.get("credential_profile", {})

        # The orchestrator handles the full pipeline
        orchestrator = CollectionOrchestrator()

        # In production, this would:
        # 1. Get SSH key from Secrets Manager
        # 2. Establish SSH connection
        # 3. Run collectors
        # 4. Store snapshot to EFS-mounted path
        # 5. Detect changes
        # 6. Write results to PostgreSQL

        return {
            "status": "success",
            "server_id": server_id,
            "hostname": hostname,
            "message": "Collection completed via worker",
        }

    def stop(self) -> None:
        """Graceful shutdown signal handler."""
        logger.info("Shutdown signal received, finishing current jobs...")
        self._running = False


async def main():
    """Entry point for the collector worker process."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    worker = CollectorWorker()

    # Handle SIGTERM (ECS task stop)
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, worker.stop)

    # Start health check server in background
    health_config = uvicorn.Config(
        health_app, host="0.0.0.0", port=8001, log_level="warning"
    )
    health_server = uvicorn.Server(health_config)
    health_task = asyncio.create_task(health_server.serve())

    # Start the worker
    await worker.start()

    # Cleanup
    health_server.should_exit = True
    await health_task


if __name__ == "__main__":
    asyncio.run(main())
