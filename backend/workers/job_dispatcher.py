"""
Collection Job Dispatcher
=========================

Publishes collection jobs to SQS for worker containers to consume.
Called by the scheduler and manual collection API endpoints.

In the single-container deployment (EC2/systemd), the scheduler
directly invokes the CollectionOrchestrator. In the ECS deployment,
it publishes jobs to SQS instead.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from backend.settings.config import get_settings

logger = logging.getLogger("scheduler")


class JobDispatcher:
    """
    Publishes collection jobs to SQS.

    The API/scheduler container uses this to dispatch work
    to the collector worker containers.

    Job message format:
    {
        "job_type": "collect" | "retry",
        "server_id": "uuid",
        "hostname": "server-name",
        "ip_address": "10.0.0.1",
        "credential_profile": {
            "secret_arn": "arn:...",
            "ssh_username": "ec2-user",
            "ssh_port": 22,
            ...
        },
        "priority": "normal" | "high",
        "requested_by": "scheduler" | "admin_username",
        "timestamp": "2026-07-25T02:00:00Z"
    }
    """

    def __init__(self):
        self._settings = get_settings()
        self._sqs_client = None
        self._queue_url = os.environ.get("SQS_QUEUE_URL")

    def _get_client(self):
        """Lazy-initialize SQS client."""
        if self._sqs_client is None:
            import boto3
            session = boto3.Session(
                region_name=self._settings.aws_region
            )
            self._sqs_client = session.client("sqs")
        return self._sqs_client

    async def dispatch_collection(
        self,
        server_id: str,
        hostname: str,
        ip_address: str,
        credential_profile: Dict[str, Any],
        job_type: str = "collect",
        requested_by: str = "scheduler",
        priority: str = "normal",
    ) -> str:
        """
        Dispatch a single collection job to SQS.

        Args:
            server_id: Server UUID.
            hostname: Server hostname.
            ip_address: Server IP for SSH connection.
            credential_profile: Profile with secret ARN and SSH config.
            job_type: "collect" or "retry".
            requested_by: Who triggered this collection.
            priority: "normal" or "high" (high = shorter delay).

        Returns:
            SQS MessageId.
        """
        import asyncio
        from datetime import datetime, timezone

        message = {
            "job_type": job_type,
            "server_id": server_id,
            "hostname": hostname,
            "ip_address": ip_address,
            "credential_profile": {
                "secret_arn": credential_profile.get("secret_arn", ""),
                "passphrase_secret_arn": credential_profile.get("passphrase_secret_arn"),
                "ssh_username": credential_profile.get("ssh_username", "ec2-user"),
                "ssh_port": credential_profile.get("ssh_port", 22),
                "connection_timeout": credential_profile.get("connection_timeout", 30),
                "command_timeout": credential_profile.get("command_timeout", 60),
            },
            "priority": priority,
            "requested_by": requested_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        loop = asyncio.get_event_loop()
        client = self._get_client()

        response = await loop.run_in_executor(
            None,
            lambda: client.send_message(
                QueueUrl=self._queue_url,
                MessageBody=json.dumps(message),
                MessageAttributes={
                    "job_type": {
                        "DataType": "String",
                        "StringValue": job_type,
                    },
                    "hostname": {
                        "DataType": "String",
                        "StringValue": hostname,
                    },
                    "priority": {
                        "DataType": "String",
                        "StringValue": priority,
                    },
                },
                # High priority = no delay; normal = 0 delay (immediate)
                DelaySeconds=0,
            ),
        )

        message_id = response["MessageId"]
        logger.info(
            f"Job dispatched: {job_type} for {hostname}",
            extra={
                "server_id": server_id,
                "message_id": message_id,
                "queue_url": self._queue_url,
            },
        )

        return message_id

    async def dispatch_batch(
        self,
        servers: List[Dict[str, Any]],
        job_type: str = "collect",
        requested_by: str = "scheduler",
    ) -> Dict[str, Any]:
        """
        Dispatch collection jobs for multiple servers.

        Uses SQS batch send for efficiency (up to 10 per batch).

        Args:
            servers: List of server dicts with id, hostname, ip_address, credential_profile.
            job_type: "collect" or "retry".
            requested_by: Who triggered this.

        Returns:
            Summary dict with successful/failed counts.
        """
        import asyncio
        from datetime import datetime, timezone

        client = self._get_client()
        loop = asyncio.get_event_loop()
        successful = 0
        failed = 0

        # Process in batches of 10 (SQS limit)
        for i in range(0, len(servers), 10):
            batch = servers[i:i + 10]
            entries = []

            for j, server in enumerate(batch):
                message = {
                    "job_type": job_type,
                    "server_id": server["id"],
                    "hostname": server["hostname"],
                    "ip_address": server["ip_address"],
                    "credential_profile": server.get("credential_profile", {}),
                    "priority": "normal",
                    "requested_by": requested_by,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                entries.append({
                    "Id": str(j),
                    "MessageBody": json.dumps(message),
                    "MessageAttributes": {
                        "job_type": {
                            "DataType": "String",
                            "StringValue": job_type,
                        },
                        "hostname": {
                            "DataType": "String",
                            "StringValue": server["hostname"],
                        },
                    },
                })

            response = await loop.run_in_executor(
                None,
                lambda: client.send_message_batch(
                    QueueUrl=self._queue_url,
                    Entries=entries,
                ),
            )

            successful += len(response.get("Successful", []))
            failed += len(response.get("Failed", []))

        logger.info(
            f"Batch dispatch complete: {successful} sent, {failed} failed",
            extra={
                "total": len(servers),
                "job_type": job_type,
                "requested_by": requested_by,
            },
        )

        return {
            "total": len(servers),
            "dispatched": successful,
            "failed": failed,
        }

    async def get_queue_depth(self) -> int:
        """Get approximate number of messages in the queue."""
        import asyncio

        client = self._get_client()
        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(
            None,
            lambda: client.get_queue_attributes(
                QueueUrl=self._queue_url,
                AttributeNames=["ApproximateNumberOfMessages"],
            ),
        )

        return int(
            response["Attributes"].get("ApproximateNumberOfMessages", 0)
        )
