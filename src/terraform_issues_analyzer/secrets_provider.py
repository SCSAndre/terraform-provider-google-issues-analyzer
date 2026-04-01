"""Secrets provider abstraction with env-default and optional GCP support."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from .logging_config import get_logger

logger = get_logger(__name__)


class EnvSecretsProvider:
    """Reads secrets directly from environment variables."""

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)


class GCPSecretsProvider:
    """Reads secrets from Google Cloud Secret Manager."""

    def __init__(self, project_id: str, secret_prefix: str = ""):
        self.project_id = project_id
        self.secret_prefix = secret_prefix

        try:
            from google.cloud import secretmanager
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError(
                "google-cloud-secret-manager is required for SECRET_BACKEND=gcp"
            ) from exc

        self._client = secretmanager.SecretManagerServiceClient()

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        secret_name = f"{self.secret_prefix}{key}"
        resource_name = (
            f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        )
        try:
            response = self._client.access_secret_version(request={"name": resource_name})
            return response.payload.data.decode("utf-8").strip()
        except Exception as exc:  # pragma: no cover - depends on cloud runtime
            logger.warning("Failed to read GCP secret '%s': %s", secret_name, exc)
            return default


class NullSecretsProvider:
    """Provider that intentionally returns no values."""

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return default


def _get_backend_name() -> str:
    return (os.getenv("SECRET_BACKEND") or "env").strip().lower()


def _allow_env_fallback() -> bool:
    return (os.getenv("SECRET_FALLBACK_TO_ENV") or "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@lru_cache(maxsize=1)
def _get_provider() -> object:
    backend = _get_backend_name()
    if backend == "env":
        return EnvSecretsProvider()

    if backend == "gcp":
        project_id = os.getenv("GCP_PROJECT_ID", "").strip()
        secret_prefix = os.getenv("GCP_SECRET_PREFIX", "")
        if not project_id:
            logger.warning("SECRET_BACKEND=gcp configured without GCP_PROJECT_ID")
            return NullSecretsProvider()
        try:
            return GCPSecretsProvider(project_id=project_id, secret_prefix=secret_prefix)
        except RuntimeError as exc:
            logger.warning("Falling back to env secrets provider: %s", exc)
            return NullSecretsProvider()

    logger.warning("Unknown SECRET_BACKEND '%s'; using env provider", backend)
    return EnvSecretsProvider()


@lru_cache(maxsize=512)
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret value from configured backend with safe env fallback."""
    provider = _get_provider()

    value = provider.get_secret(key, default=None)
    if value not in (None, ""):
        return value

    # Keep env fallback on by default for non-breaking behavior.
    if _get_backend_name() != "env" and _allow_env_fallback():
        fallback = os.getenv(key, default)
        if fallback not in (None, ""):
            logger.info("Using env fallback for secret '%s'", key)
        return fallback

    return default


def clear_secret_cache() -> None:
    """Clear provider and value caches (primarily for tests)."""
    _get_provider.cache_clear()
    get_secret.cache_clear()

