"""
Secrets Management
==================

Pluggable secrets provider framework.
Secrets are retrieved at runtime and held only in memory.
They are never logged, persisted to disk, or returned in API responses.
"""

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from backend.settings.config import get_settings

logger = logging.getLogger("security")


class SecretsProvider(ABC):
    """
    Abstract base class for secrets providers.
    
    All secrets providers must implement get_secret and
    optionally put_secret for secret rotation.
    
    Secrets MUST:
    - Never appear in logs
    - Never appear in API responses
    - Never be written to disk
    - Remain only in application memory
    """
    
    @abstractmethod
    async def get_secret(self, secret_id: str) -> str:
        """
        Retrieve a secret value by its identifier.
        
        Args:
            secret_id: The identifier (ARN, path, or key name).
        
        Returns:
            str: The secret value (private key, password, etc.).
        
        Raises:
            SecretNotFoundError: If the secret doesn't exist.
            SecretAccessDeniedError: If access is denied.
        """
        ...
    
    @abstractmethod
    async def put_secret(
        self, secret_id: str, value: str
    ) -> None:
        """
        Store or update a secret value.
        
        Args:
            secret_id: The identifier for the secret.
            value: The secret value to store.
        """
        ...
    
    @abstractmethod
    async def delete_secret(self, secret_id: str) -> None:
        """
        Delete a secret.
        
        Args:
            secret_id: The identifier for the secret.
        """
        ...
    
    @abstractmethod
    async def list_secrets(
        self, prefix: Optional[str] = None
    ) -> list:
        """
        List available secrets, optionally filtered by prefix.
        
        Args:
            prefix: Optional prefix filter.
        
        Returns:
            List of secret identifiers (NOT values).
        """
        ...


class AWSSecretsManagerProvider(SecretsProvider):
    """
    AWS Secrets Manager implementation.
    
    Uses boto3 to retrieve secrets from AWS Secrets Manager.
    Supports IAM role-based authentication.
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        profile: Optional[str] = None,
    ):
        self._region = region
        self._profile = profile
        self._client = None
    
    def _get_client(self):
        """Lazy-initialize the boto3 Secrets Manager client."""
        if self._client is None:
            import boto3
            
            session_kwargs = {"region_name": self._region}
            if self._profile:
                session_kwargs["profile_name"] = self._profile
            
            session = boto3.Session(**session_kwargs)
            self._client = session.client("secretsmanager")
        
        return self._client
    
    async def get_secret(self, secret_id: str) -> str:
        """Retrieve a secret from AWS Secrets Manager."""
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        def _fetch():
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_id)
            return response["SecretString"]
        
        try:
            value = await loop.run_in_executor(None, _fetch)
            logger.info(
                "Secret retrieved successfully",
                extra={"secret_id": secret_id[:20] + "..."},
            )
            return value
        except Exception as e:
            logger.error(
                "Failed to retrieve secret",
                extra={
                    "secret_id": secret_id[:20] + "...",
                    "error_type": type(e).__name__,
                },
            )
            raise
    
    async def put_secret(
        self, secret_id: str, value: str
    ) -> None:
        """Store or update a secret in AWS Secrets Manager."""
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        def _store():
            client = self._get_client()
            client.put_secret_value(
                SecretId=secret_id,
                SecretString=value,
            )
        
        await loop.run_in_executor(None, _store)
        logger.info(
            "Secret stored successfully",
            extra={"secret_id": secret_id[:20] + "..."},
        )
    
    async def delete_secret(self, secret_id: str) -> None:
        """Delete a secret from AWS Secrets Manager."""
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        def _delete():
            client = self._get_client()
            client.delete_secret(
                SecretId=secret_id,
                ForceDeleteWithoutRecovery=False,
            )
        
        await loop.run_in_executor(None, _delete)
    
    async def list_secrets(
        self, prefix: Optional[str] = None
    ) -> list:
        """List secrets in AWS Secrets Manager."""
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        def _list():
            client = self._get_client()
            paginator = client.get_paginator("list_secrets")
            secrets = []
            
            filters = []
            if prefix:
                filters.append(
                    {"Key": "name", "Values": [prefix]}
                )
            
            kwargs = {}
            if filters:
                kwargs["Filters"] = filters
            
            for page in paginator.paginate(**kwargs):
                for secret in page.get("SecretList", []):
                    secrets.append(secret["Name"])
            
            return secrets
        
        return await loop.run_in_executor(None, _list)


class LocalSecretsProvider(SecretsProvider):
    """
    Local file-based secrets provider for development only.
    
    WARNING: This provider stores secrets in a local directory.
    It should NEVER be used in production environments.
    """
    
    def __init__(self, secrets_dir: str = ".secrets"):
        import os
        self._secrets_dir = secrets_dir
        os.makedirs(secrets_dir, exist_ok=True)
        logger.warning(
            "Using local secrets provider - "
            "NOT suitable for production!"
        )
    
    async def get_secret(self, secret_id: str) -> str:
        """Read a secret from local file."""
        import os
        
        # Sanitize the secret_id for filesystem
        safe_name = secret_id.replace("/", "_").replace(":", "_")
        path = os.path.join(self._secrets_dir, safe_name)
        
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Secret not found: {secret_id}"
            )
        
        with open(path, "r") as f:
            return f.read().strip()
    
    async def put_secret(
        self, secret_id: str, value: str
    ) -> None:
        """Write a secret to local file."""
        import os
        
        safe_name = secret_id.replace("/", "_").replace(":", "_")
        path = os.path.join(self._secrets_dir, safe_name)
        
        with open(path, "w") as f:
            f.write(value)
        
        # Set restrictive permissions
        os.chmod(path, 0o600)
    
    async def delete_secret(self, secret_id: str) -> None:
        """Delete a local secret file."""
        import os
        
        safe_name = secret_id.replace("/", "_").replace(":", "_")
        path = os.path.join(self._secrets_dir, safe_name)
        
        if os.path.exists(path):
            os.remove(path)
    
    async def list_secrets(
        self, prefix: Optional[str] = None
    ) -> list:
        """List local secret files."""
        import os
        
        secrets = os.listdir(self._secrets_dir)
        if prefix:
            safe_prefix = prefix.replace("/", "_").replace(":", "_")
            secrets = [s for s in secrets if s.startswith(safe_prefix)]
        return secrets


@lru_cache()
def get_secrets_provider() -> SecretsProvider:
    """
    Factory function to create the configured secrets provider.
    
    Returns the appropriate provider based on application settings.
    
    Returns:
        SecretsProvider: Configured secrets provider instance.
    """
    settings = get_settings()
    
    if settings.secrets_provider == "aws_secrets_manager":
        return AWSSecretsManagerProvider(
            region=settings.aws_region,
            profile=settings.aws_profile,
        )
    elif settings.secrets_provider == "local":
        return LocalSecretsProvider()
    else:
        raise ValueError(
            f"Unknown secrets provider: {settings.secrets_provider}"
        )
