"""
Sandbox factory for managing different sandbox providers.

Provides automatic provider selection based on configuration:
- Docker (default for local deployments)
- E2B (for cloud deployments)
- Daytona (legacy, deprecated)

Usage:
    factory = SandboxFactory()
    adapter = await factory.get_adapter()
    sandbox = await adapter.create_sandbox()
"""

import os
from typing import Optional
from enum import Enum

from .adapter import SandboxAdapter, SandboxProvider
from .adapters.docker_sandbox import DockerSandboxAdapter
from core.utils.logger import logger


class SandboxFactory:
    """
    Factory for creating sandbox adapters based on configuration.
    
    Configuration priority:
    1. SANDBOX_PROVIDER environment variable
    2. CLOUD_PROVIDER environment variable (maps to sandbox provider)
    3. Auto-detect based on available configurations
    4. Default to Docker
    """
    
    _instance: Optional['SandboxFactory'] = None
    _adapter: Optional[SandboxAdapter] = None
    
    def __init__(self):
        self.provider = self._detect_provider()
        logger.info(f"Sandbox factory initialized with provider: {self.provider.value}")
    
    @classmethod
    def get_instance(cls) -> 'SandboxFactory':
        """Get singleton factory instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _detect_provider(self) -> SandboxProvider:
        """
        Detect which sandbox provider to use.
        
        Checks environment variables and availability of services.
        """
        # Check explicit SANDBOX_PROVIDER setting
        provider_env = os.getenv("SANDBOX_PROVIDER", "").lower()
        if provider_env == "docker":
            return SandboxProvider.DOCKER
        elif provider_env == "e2b":
            return SandboxProvider.E2B
        elif provider_env == "daytona":
            logger.warning("Daytona is deprecated, consider migrating to Docker or E2B")
            return SandboxProvider.DAYTONA
        
        # Check CLOUD_PROVIDER and map to sandbox provider
        cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()
        if cloud_provider in ["aliyun", "tencent", "local"]:
            # China deployments or local → use Docker
            return SandboxProvider.DOCKER
        elif cloud_provider == "supabase":
            # International cloud → check if E2B is configured
            if os.getenv("E2B_API_KEY"):
                return SandboxProvider.E2B
            # Fall back to Docker if no E2B key
            return SandboxProvider.DOCKER
        
        # Auto-detect based on configuration availability
        if os.getenv("E2B_API_KEY"):
            logger.info("E2B API key found, using E2B sandboxes")
            return SandboxProvider.E2B
        
        if os.getenv("DAYTONA_API_KEY"):
            logger.warning("Daytona API key found, but Daytona is deprecated")
            logger.warning("Consider migrating to Docker or E2B")
            return SandboxProvider.DAYTONA
        
        # Default to Docker (works offline, China-friendly)
        logger.info("Defaulting to Docker sandbox provider")
        return SandboxProvider.DOCKER
    
    async def get_adapter(self) -> SandboxAdapter:
        """
        Get the sandbox adapter instance.
        
        Creates adapter lazily and caches it.
        
        Returns:
            Configured SandboxAdapter instance
        """
        if self._adapter is not None:
            return self._adapter
        
        if self.provider == SandboxProvider.DOCKER:
            self._adapter = self._create_docker_adapter()
        elif self.provider == SandboxProvider.E2B:
            self._adapter = self._create_e2b_adapter()
        elif self.provider == SandboxProvider.DAYTONA:
            self._adapter = self._create_daytona_adapter()
        else:
            raise ValueError(f"Unknown sandbox provider: {self.provider}")
        
        # Validate adapter is configured
        if not self._adapter.is_configured():
            raise RuntimeError(
                f"Sandbox provider '{self.provider.value}' is not properly configured. "
                f"Please check your environment variables and service availability."
            )
        
        return self._adapter
    
    def _create_docker_adapter(self) -> DockerSandboxAdapter:
        """Create Docker sandbox adapter."""
        return DockerSandboxAdapter(
            docker_url=os.getenv("DOCKER_HOST"),
            image=os.getenv("SANDBOX_IMAGE", "kortix-sandbox:latest"),
            network=os.getenv("SANDBOX_NETWORK"),
            memory_limit=os.getenv("SANDBOX_MEMORY_LIMIT", "512m"),
            cpu_limit=float(os.getenv("SANDBOX_CPU_LIMIT", "1.0")),
            enable_gpu=os.getenv("SANDBOX_ENABLE_GPU", "false").lower() == "true",
        )
    
    def _create_e2b_adapter(self) -> SandboxAdapter:
        """Create E2B sandbox adapter."""
        # TODO: Implement E2B adapter when needed
        # from .adapters.e2b_sandbox import E2BSandboxAdapter
        # return E2BSandboxAdapter(
        #     api_key=os.getenv("E2B_API_KEY"),
        # )
        raise NotImplementedError("E2B adapter not yet implemented")
    
    def _create_daytona_adapter(self) -> SandboxAdapter:
        """Create Daytona sandbox adapter (legacy)."""
        # TODO: Create Daytona adapter wrapper if needed for migration
        # from .adapters.daytona_sandbox import DaytonaSandboxAdapter
        # return DaytonaSandboxAdapter(
        #     api_key=os.getenv("DAYTONA_API_KEY"),
        #     server_url=os.getenv("DAYTONA_SERVER_URL"),
        #     target=os.getenv("DAYTONA_TARGET"),
        # )
        raise NotImplementedError(
            "Daytona adapter not implemented. "
            "Please migrate to Docker or E2B. "
            "Set SANDBOX_PROVIDER=docker to use Docker sandboxes."
        )
    
    def get_provider_name(self) -> str:
        """Get the current provider name."""
        return self.provider.value


# Convenience function for getting sandbox adapter
async def get_sandbox_adapter() -> SandboxAdapter:
    """
    Get the configured sandbox adapter.
    
    This is the main entry point for getting a sandbox adapter.
    
    Returns:
        Configured SandboxAdapter instance
    """
    factory = SandboxFactory.get_instance()
    return await factory.get_adapter()
