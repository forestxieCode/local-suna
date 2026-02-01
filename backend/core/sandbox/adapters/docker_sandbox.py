"""
Docker-based sandbox adapter for local/self-hosted deployments.

Uses Docker containers to provide isolated code execution environments.
Ideal for local development, testing, and private deployments.

Features:
- Isolated Docker containers
- File system operations
- Command execution
- Resource limits
- Browser automation support (via Playwright)
- No external dependencies (works offline)
"""

import asyncio
import docker
import docker.errors
import tempfile
import tarfile
import io
import os
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..adapter import (
    SandboxAdapter,
    SandboxInfo,
    SandboxState,
    ExecuteResult,
    FileInfo
)
from core.utils.logger import logger


class DockerSandboxAdapter(SandboxAdapter):
    """
    Docker-based sandbox implementation.
    
    Each sandbox is a Docker container with:
    - Python 3.11+ runtime
    - Node.js 20+ runtime
    - Playwright for browser automation
    - Isolated filesystem
    - Resource limits
    """
    
    DEFAULT_IMAGE = "kortix-sandbox:latest"
    DEFAULT_TIMEOUT = 300  # 5 minutes
    
    def __init__(
        self,
        docker_url: Optional[str] = None,
        image: Optional[str] = None,
        network: Optional[str] = None,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
        enable_gpu: bool = False
    ):
        """
        Initialize Docker sandbox adapter.
        
        Args:
            docker_url: Docker daemon URL (default: auto-detect)
            image: Docker image to use (default: kortix-sandbox:latest)
            network: Docker network to use (default: bridge)
            memory_limit: Memory limit per container (default: 512m)
            cpu_limit: CPU limit per container (default: 1.0 = 1 core)
            enable_gpu: Enable GPU access (requires nvidia-docker)
        """
        self.docker_url = docker_url or os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
        self.image = image or os.getenv("SANDBOX_IMAGE", self.DEFAULT_IMAGE)
        self.network = network or os.getenv("SANDBOX_NETWORK", "bridge")
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.enable_gpu = enable_gpu
        
        # Initialize Docker client
        try:
            self.client = docker.DockerClient(base_url=self.docker_url)
            # Test connection
            self.client.ping()
            logger.info(f"Docker sandbox adapter initialized: {self.docker_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None
    
    async def create_sandbox(
        self,
        snapshot_id: Optional[str] = None,
        resources: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SandboxInfo:
        """Create a new Docker container sandbox."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        # Use snapshot_id as image name if provided
        image = snapshot_id or self.image
        
        # Parse resources
        memory = resources.get("memory", self.memory_limit) if resources else self.memory_limit
        cpu_quota = int(resources.get("cpu", self.cpu_limit) * 100000) if resources else int(self.cpu_limit * 100000)
        
        # Container configuration
        container_config = {
            "image": image,
            "detach": True,
            "network": self.network,
            "mem_limit": memory,
            "cpu_period": 100000,
            "cpu_quota": cpu_quota,
            "environment": {
                "DEBIAN_FRONTEND": "noninteractive",
            },
            "labels": {
                "kortix.sandbox": "true",
                "kortix.created_at": str(time.time()),
            },
            # Keep container running
            "command": ["/bin/bash", "-c", "tail -f /dev/null"],
            "stdin_open": True,
            "tty": True,
        }
        
        # Add GPU support if enabled
        if self.enable_gpu:
            container_config["device_requests"] = [
                docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])
            ]
        
        # Add metadata as labels
        if metadata:
            for key, value in metadata.items():
                container_config["labels"][f"kortix.meta.{key}"] = str(value)
        
        try:
            # Run in executor since docker-py is sync
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.run(**container_config)
            )
            
            logger.info(f"Created Docker sandbox: {container.id[:12]}")
            
            # Wait for container to be ready
            await asyncio.sleep(0.5)
            
            return SandboxInfo(
                sandbox_id=container.id,
                state=SandboxState.STARTED,
                metadata=metadata or {},
            )
            
        except docker.errors.ImageNotFound:
            logger.error(f"Docker image not found: {image}")
            raise RuntimeError(f"Docker image '{image}' not found. Please build it first.")
        except Exception as e:
            logger.error(f"Failed to create Docker sandbox: {e}")
            raise
    
    async def get_sandbox(self, sandbox_id: str) -> SandboxInfo:
        """Get information about a Docker container sandbox."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            # Map Docker status to SandboxState
            status = container.status.lower()
            if status == "running":
                state = SandboxState.STARTED
            elif status in ["created", "restarting"]:
                state = SandboxState.CREATING
            elif status in ["paused", "exited"]:
                state = SandboxState.STOPPED
            else:
                state = SandboxState.ERROR
            
            # Extract metadata from labels
            labels = container.labels or {}
            metadata = {}
            for key, value in labels.items():
                if key.startswith("kortix.meta."):
                    meta_key = key.replace("kortix.meta.", "")
                    metadata[meta_key] = value
            
            return SandboxInfo(
                sandbox_id=container.id,
                state=state,
                metadata=metadata,
            )
            
        except docker.errors.NotFound:
            logger.error(f"Docker container not found: {sandbox_id}")
            raise RuntimeError(f"Sandbox {sandbox_id} not found")
        except Exception as e:
            logger.error(f"Failed to get Docker sandbox: {e}")
            raise
    
    async def start_sandbox(self, sandbox_id: str) -> SandboxInfo:
        """Start a stopped Docker container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            if container.status != "running":
                await loop.run_in_executor(None, container.start)
                logger.info(f"Started Docker sandbox: {sandbox_id[:12]}")
                await asyncio.sleep(0.5)  # Wait for startup
            
            return await self.get_sandbox(sandbox_id)
            
        except Exception as e:
            logger.error(f"Failed to start Docker sandbox: {e}")
            raise
    
    async def stop_sandbox(self, sandbox_id: str) -> SandboxInfo:
        """Stop a running Docker container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            if container.status == "running":
                await loop.run_in_executor(
                    None,
                    lambda: container.stop(timeout=10)
                )
                logger.info(f"Stopped Docker sandbox: {sandbox_id[:12]}")
            
            return await self.get_sandbox(sandbox_id)
            
        except Exception as e:
            logger.error(f"Failed to stop Docker sandbox: {e}")
            raise
    
    async def delete_sandbox(self, sandbox_id: str) -> None:
        """Delete a Docker container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            # Stop if running
            if container.status == "running":
                await loop.run_in_executor(
                    None,
                    lambda: container.stop(timeout=5)
                )
            
            # Remove container
            await loop.run_in_executor(
                None,
                lambda: container.remove(force=True)
            )
            
            logger.info(f"Deleted Docker sandbox: {sandbox_id[:12]}")
            
        except docker.errors.NotFound:
            logger.warning(f"Docker container already deleted: {sandbox_id}")
        except Exception as e:
            logger.error(f"Failed to delete Docker sandbox: {e}")
            raise
    
    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ExecuteResult:
        """Execute a command in the Docker container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            # Prepare exec command
            exec_config = {
                "cmd": ["/bin/bash", "-c", command],
                "workdir": working_dir or "/workspace",
                "environment": env or {},
                "stream": False,
                "demux": True,  # Separate stdout and stderr
            }
            
            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: container.exec_run(**exec_config)
                    ),
                    timeout=timeout
                )
                
                exit_code = result.exit_code
                stdout_bytes, stderr_bytes = result.output
                
                stdout = stdout_bytes.decode('utf-8') if stdout_bytes else ""
                stderr = stderr_bytes.decode('utf-8') if stderr_bytes else ""
                
                return ExecuteResult(
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    success=(exit_code == 0),
                )
                
            except asyncio.TimeoutError:
                logger.error(f"Command execution timeout after {timeout}s")
                return ExecuteResult(
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command timeout after {timeout} seconds",
                    success=False,
                    error="Timeout"
                )
            
        except Exception as e:
            logger.error(f"Failed to execute command in Docker sandbox: {e}")
            return ExecuteResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                success=False,
                error=str(e)
            )
    
    async def write_file(
        self,
        sandbox_id: str,
        path: str,
        content: bytes,
        mode: int = 0o644
    ) -> None:
        """Write a file to the Docker container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            # Create tar archive with the file
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                # Create file info
                tarinfo = tarfile.TarInfo(name=os.path.basename(path))
                tarinfo.size = len(content)
                tarinfo.mode = mode
                tarinfo.mtime = int(time.time())
                
                # Add file to archive
                tar.addfile(tarinfo, io.BytesIO(content))
            
            tar_stream.seek(0)
            tar_data = tar_stream.read()
            
            # Upload to container
            dest_dir = os.path.dirname(path) or "/"
            await loop.run_in_executor(
                None,
                lambda: container.put_archive(dest_dir, tar_data)
            )
            
            logger.debug(f"Wrote file to Docker sandbox: {path}")
            
        except Exception as e:
            logger.error(f"Failed to write file to Docker sandbox: {e}")
            raise
    
    async def read_file(
        self,
        sandbox_id: str,
        path: str
    ) -> bytes:
        """Read a file from the Docker container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            # Get tar archive from container
            tar_stream, _ = await loop.run_in_executor(
                None,
                lambda: container.get_archive(path)
            )
            
            # Extract file from tar
            tar_data = b"".join(tar_stream)
            tar_file = tarfile.open(fileobj=io.BytesIO(tar_data))
            
            # Get first file from archive
            member = tar_file.next()
            if member:
                file_obj = tar_file.extractfile(member)
                content = file_obj.read() if file_obj else b""
                return content
            
            raise FileNotFoundError(f"File not found: {path}")
            
        except Exception as e:
            logger.error(f"Failed to read file from Docker sandbox: {e}")
            raise
    
    async def list_files(
        self,
        sandbox_id: str,
        path: str = "/"
    ) -> List[FileInfo]:
        """List files in a directory."""
        # Execute 'ls -la' command and parse output
        result = await self.execute_command(
            sandbox_id,
            f"ls -la --time-style=+%s {path}",
            timeout=10
        )
        
        if not result.success:
            return []
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line or line.startswith('total'):
                continue
            
            parts = line.split()
            if len(parts) < 9:
                continue
            
            permissions = parts[0]
            size = int(parts[4])
            mtime = float(parts[5])
            name = ' '.join(parts[8:])
            
            if name in ['.', '..']:
                continue
            
            files.append(FileInfo(
                path=os.path.join(path, name),
                size=size,
                is_directory=permissions.startswith('d'),
                modified_time=mtime
            ))
        
        return files
    
    async def delete_file(
        self,
        sandbox_id: str,
        path: str
    ) -> None:
        """Delete a file or directory."""
        result = await self.execute_command(
            sandbox_id,
            f"rm -rf {path}",
            timeout=30
        )
        
        if not result.success:
            raise RuntimeError(f"Failed to delete {path}: {result.stderr}")
    
    async def health_check(self, sandbox_id: str) -> bool:
        """Check if container is healthy."""
        try:
            info = await self.get_sandbox(sandbox_id)
            return info.state == SandboxState.STARTED
        except:
            return False
    
    async def get_resource_usage(
        self,
        sandbox_id: str
    ) -> Dict[str, Any]:
        """Get container resource usage."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                sandbox_id
            )
            
            stats = await loop.run_in_executor(
                None,
                lambda: container.stats(stream=False)
            )
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                        stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
            
            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_bytes": memory_usage,
                "memory_limit_bytes": memory_limit,
                "memory_percent": round(memory_percent, 2),
            }
            
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return {}
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Docker"
    
    def is_configured(self) -> bool:
        """Check if Docker is available."""
        return self.client is not None
