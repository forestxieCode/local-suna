"""
Wrapper to adapt the new sandbox adapter system to the existing Daytona-based interface.

This provides backward compatibility while enabling use of the new adapter system.
Existing code can continue using AsyncSandbox-like interface while actually using
Docker or other adapters under the hood.
"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .adapter import SandboxAdapter, SandboxInfo as AdapterSandboxInfo, ExecuteResult
from .factory import get_sandbox_adapter
from core.utils.logger import logger


@dataclass
class SandboxInfo:
    """
    Compatibility wrapper for SandboxInfo.
    
    Maintains the same interface as before but uses new adapter system.
    """
    sandbox_id: str
    sandbox: 'CompatSandbox'
    password: str
    sandbox_url: Optional[str] = None
    vnc_preview: Optional[str] = None
    token: Optional[str] = None


class CompatSandbox:
    """
    Compatibility wrapper for AsyncSandbox.
    
    Provides the same interface as Daytona's AsyncSandbox but uses
    the new adapter system under the hood.
    """
    
    def __init__(self, adapter: SandboxAdapter, sandbox_id: str, metadata: Dict[str, Any] = None):
        self.adapter = adapter
        self.id = sandbox_id
        self.sandbox_id = sandbox_id
        self.metadata = metadata or {}
        self._state = None
    
    async def get_state(self):
        """Get current sandbox state."""
        if self._state is None:
            info = await self.adapter.get_sandbox(self.sandbox_id)
            self._state = info.state
        return self._state
    
    @property
    def state(self):
        """Synchronous state property (may be stale)."""
        return self._state
    
    # File operations compatibility
    
    class FileOperations:
        """Compatibility wrapper for sandbox.files operations."""
        
        def __init__(self, adapter: SandboxAdapter, sandbox_id: str):
            self.adapter = adapter
            self.sandbox_id = sandbox_id
        
        async def write(self, path: str, content: bytes) -> None:
            """Write file to sandbox."""
            await self.adapter.write_file(self.sandbox_id, path, content)
        
        async def read(self, path: str) -> bytes:
            """Read file from sandbox."""
            return await self.adapter.read_file(self.sandbox_id, path)
        
        async def list(self, path: str = "/") -> list:
            """List files in directory."""
            files = await self.adapter.list_files(self.sandbox_id, path)
            # Convert FileInfo to dict for compatibility
            return [
                {
                    'path': f.path,
                    'size': f.size,
                    'is_directory': f.is_directory,
                    'modified_time': f.modified_time
                }
                for f in files
            ]
        
        async def remove(self, path: str) -> None:
            """Delete file or directory."""
            await self.adapter.delete_file(self.sandbox_id, path)
    
    @property
    def files(self):
        """File operations interface."""
        return self.FileOperations(self.adapter, self.sandbox_id)
    
    # Process/execution compatibility
    
    class ProcessOperations:
        """Compatibility wrapper for sandbox.process operations."""
        
        def __init__(self, adapter: SandboxAdapter, sandbox_id: str):
            self.adapter = adapter
            self.sandbox_id = sandbox_id
            self._sessions = {}
        
        async def execute(
            self,
            command: str,
            working_dir: Optional[str] = None,
            env: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = None
        ) -> ExecuteResult:
            """Execute a command."""
            return await self.adapter.execute_command(
                self.sandbox_id,
                command,
                working_dir=working_dir,
                env=env,
                timeout=timeout
            )
        
        async def create_session(self, session_id: str) -> None:
            """Create a session (no-op for compatibility)."""
            self._sessions[session_id] = {'id': session_id, 'active': True}
            logger.debug(f"Created session: {session_id}")
        
        async def execute_session_command(
            self,
            session_id: str,
            request: Any
        ) -> ExecuteResult:
            """Execute command in session."""
            # Extract command from request
            if hasattr(request, 'command'):
                command = request.command
            elif isinstance(request, dict):
                command = request.get('command', '')
            else:
                command = str(request)
            
            return await self.execute(command)
    
    @property
    def process(self):
        """Process operations interface."""
        return self.ProcessOperations(self.adapter, self.sandbox_id)


async def get_or_start_sandbox(sandbox_id: str) -> CompatSandbox:
    """
    Retrieve a sandbox by ID and ensure it's started.
    
    This maintains compatibility with the existing Daytona-based interface
    but uses the new adapter system.
    
    Args:
        sandbox_id: ID of the sandbox
        
    Returns:
        CompatSandbox instance
    """
    logger.info(f"Getting or starting sandbox with ID: {sandbox_id}")
    
    try:
        # Get adapter from factory
        adapter = await get_sandbox_adapter()
        
        # Get sandbox info
        info = await adapter.get_sandbox(sandbox_id)
        
        # Check if sandbox needs to be started
        from .adapter import SandboxState
        if info.state in [SandboxState.STOPPED, SandboxState.ARCHIVED]:
            logger.info(f"Sandbox is in {info.state} state. Starting...")
            await adapter.start_sandbox(sandbox_id)
            
            # Wait for sandbox to be ready
            for _ in range(30):
                await asyncio.sleep(1)
                info = await adapter.get_sandbox(sandbox_id)
                if info.state == SandboxState.STARTED:
                    break
        
        logger.info(f"Sandbox {sandbox_id} is ready")
        
        # Return compatibility wrapper
        return CompatSandbox(adapter, sandbox_id, info.metadata)
        
    except Exception as e:
        logger.error(f"Error retrieving or starting sandbox: {str(e)}")
        raise


async def create_sandbox(
    password: str,
    project_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> CompatSandbox:
    """
    Create a new sandbox.
    
    This maintains compatibility with the existing Daytona-based interface
    but uses the new adapter system.
    
    Args:
        password: Password for VNC/browser access (stored in metadata)
        project_id: Optional project ID for labeling
        metadata: Additional metadata
        
    Returns:
        CompatSandbox instance
    """
    logger.info("Creating new sandbox environment")
    
    try:
        # Get adapter from factory
        adapter = await get_sandbox_adapter()
        
        # Prepare metadata
        meta = metadata or {}
        meta['password'] = password
        if project_id:
            meta['project_id'] = project_id
        
        # Create sandbox through adapter
        info = await adapter.create_sandbox(
            metadata=meta
        )
        
        logger.info(f"Created sandbox: {info.sandbox_id}")
        
        # Return compatibility wrapper
        return CompatSandbox(adapter, info.sandbox_id, info.metadata)
        
    except Exception as e:
        logger.error(f"Error creating sandbox: {str(e)}")
        raise


# Backward compatibility for imports
try:
    from daytona_sdk import SandboxState, SessionExecuteRequest
    logger.debug("Daytona SDK available, using original implementation for compatibility")
except ImportError:
    # Daytona not available, provide compatibility classes
    logger.info("Daytona SDK not available, using adapter-based compatibility layer")
    
    class SandboxState:
        """Compatibility enum for SandboxState."""
        CREATING = "creating"
        STARTED = "started"
        STOPPED = "stopped"
        ARCHIVING = "archiving"
        ARCHIVED = "archived"
        ERROR = "error"
    
    @dataclass
    class SessionExecuteRequest:
        """Compatibility class for SessionExecuteRequest."""
        command: str
        var_async: bool = False
