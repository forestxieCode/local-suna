"""
Sandbox adapter interface for code execution environments.

Provides abstraction layer for different sandbox providers:
- Docker (local/self-hosted)
- E2B (cloud)
- Daytona (legacy, to be deprecated)

This allows switching between sandbox providers based on deployment needs.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class SandboxState(Enum):
    """Sandbox lifecycle states."""
    CREATING = "creating"
    STARTED = "started"
    STOPPED = "stopped"
    ARCHIVING = "archiving"
    ARCHIVED = "archived"
    ERROR = "error"


class SandboxProvider(Enum):
    """Available sandbox providers."""
    DOCKER = "docker"        # Local Docker containers
    E2B = "e2b"              # E2B cloud sandboxes
    DAYTONA = "daytona"      # Legacy Daytona (deprecated)


@dataclass
class SandboxInfo:
    """Complete sandbox information."""
    sandbox_id: str
    state: SandboxState
    password: Optional[str] = None
    sandbox_url: Optional[str] = None
    vnc_preview: Optional[str] = None
    token: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecuteResult:
    """Result of a command execution."""
    exit_code: int
    stdout: str
    stderr: str
    success: bool = True
    error: Optional[str] = None
    
    @property
    def output(self) -> str:
        """Combined output."""
        return self.stdout + self.stderr


@dataclass
class FileInfo:
    """Information about a file in sandbox."""
    path: str
    size: int
    is_directory: bool
    modified_time: Optional[float] = None


class SandboxAdapter(ABC):
    """
    Abstract base class for sandbox adapters.
    
    Defines the interface that all sandbox providers must implement.
    """
    
    @abstractmethod
    async def create_sandbox(
        self,
        snapshot_id: Optional[str] = None,
        resources: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SandboxInfo:
        """
        Create a new sandbox instance.
        
        Args:
            snapshot_id: Optional snapshot/image to create from
            resources: Resource limits (CPU, memory, disk)
            metadata: Additional metadata for the sandbox
            
        Returns:
            SandboxInfo with details about created sandbox
        """
        pass
    
    @abstractmethod
    async def get_sandbox(self, sandbox_id: str) -> SandboxInfo:
        """
        Get information about an existing sandbox.
        
        Args:
            sandbox_id: ID of the sandbox
            
        Returns:
            SandboxInfo with current sandbox state
        """
        pass
    
    @abstractmethod
    async def start_sandbox(self, sandbox_id: str) -> SandboxInfo:
        """
        Start a stopped sandbox.
        
        Args:
            sandbox_id: ID of the sandbox to start
            
        Returns:
            Updated SandboxInfo
        """
        pass
    
    @abstractmethod
    async def stop_sandbox(self, sandbox_id: str) -> SandboxInfo:
        """
        Stop a running sandbox.
        
        Args:
            sandbox_id: ID of the sandbox to stop
            
        Returns:
            Updated SandboxInfo
        """
        pass
    
    @abstractmethod
    async def delete_sandbox(self, sandbox_id: str) -> None:
        """
        Permanently delete a sandbox.
        
        Args:
            sandbox_id: ID of the sandbox to delete
        """
        pass
    
    @abstractmethod
    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ExecuteResult:
        """
        Execute a command in the sandbox.
        
        Args:
            sandbox_id: ID of the sandbox
            command: Command to execute
            working_dir: Working directory for execution
            env: Environment variables
            timeout: Execution timeout in seconds
            
        Returns:
            ExecuteResult with command output
        """
        pass
    
    @abstractmethod
    async def write_file(
        self,
        sandbox_id: str,
        path: str,
        content: bytes,
        mode: int = 0o644
    ) -> None:
        """
        Write a file to the sandbox filesystem.
        
        Args:
            sandbox_id: ID of the sandbox
            path: Path in sandbox filesystem
            content: File content as bytes
            mode: File permissions (Unix-style)
        """
        pass
    
    @abstractmethod
    async def read_file(
        self,
        sandbox_id: str,
        path: str
    ) -> bytes:
        """
        Read a file from the sandbox filesystem.
        
        Args:
            sandbox_id: ID of the sandbox
            path: Path in sandbox filesystem
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    async def list_files(
        self,
        sandbox_id: str,
        path: str = "/"
    ) -> List[FileInfo]:
        """
        List files in a directory.
        
        Args:
            sandbox_id: ID of the sandbox
            path: Directory path
            
        Returns:
            List of FileInfo objects
        """
        pass
    
    @abstractmethod
    async def delete_file(
        self,
        sandbox_id: str,
        path: str
    ) -> None:
        """
        Delete a file or directory.
        
        Args:
            sandbox_id: ID of the sandbox
            path: Path to delete
        """
        pass
    
    # Browser automation support (optional, not all providers support this)
    
    async def get_browser_url(self, sandbox_id: str) -> Optional[str]:
        """
        Get URL for browser automation (if supported).
        
        Args:
            sandbox_id: ID of the sandbox
            
        Returns:
            Browser URL or None if not supported
        """
        return None
    
    async def take_screenshot(
        self,
        sandbox_id: str,
        url: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Take a screenshot of browser (if supported).
        
        Args:
            sandbox_id: ID of the sandbox
            url: URL to navigate to before screenshot
            
        Returns:
            Screenshot as PNG bytes or None if not supported
        """
        return None
    
    # Health and monitoring
    
    @abstractmethod
    async def health_check(self, sandbox_id: str) -> bool:
        """
        Check if sandbox is healthy and responsive.
        
        Args:
            sandbox_id: ID of the sandbox
            
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_resource_usage(
        self,
        sandbox_id: str
    ) -> Dict[str, Any]:
        """
        Get current resource usage stats.
        
        Args:
            sandbox_id: ID of the sandbox
            
        Returns:
            Dict with CPU, memory, disk usage
        """
        pass
    
    # Provider info
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        pass
