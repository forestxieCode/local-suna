"""Docker 沙箱 - 代码执行环境"""
import docker
from docker.models.containers import Container
from typing import Dict, Any, Optional
import time
from core.utils.logger import get_logger
from core.utils.config import get_config

logger = get_logger(__name__)


class SandboxResult:
    """沙箱执行结果"""
    def __init__(self, success: bool, output: str, error: str = "", exit_code: int = 0):
        self.success = success
        self.output = output
        self.error = error
        self.exit_code = exit_code
    
    def __str__(self):
        if self.success:
            return f"✅ 执行成功\n输出:\n{self.output}"
        else:
            return f"❌ 执行失败 (exit code: {self.exit_code})\n错误:\n{self.error}"


class DockerSandbox:
    """Docker 沙箱执行器"""
    
    def __init__(self, image: Optional[str] = None, timeout: Optional[int] = None, memory_limit: Optional[int] = None):
        config = get_config()
        
        self.image = image or config.sandbox_image
        self.timeout = timeout or config.sandbox_timeout
        self.memory_limit_mb = memory_limit or config.sandbox_memory_limit
        
        try:
            self.client = docker.from_env()
            logger.info("Docker 客户端初始化成功")
        except Exception as e:
            logger.error("Docker 客户端初始化失败", error=str(e))
            raise Exception(f"无法连接到 Docker。请确保 Docker 已安装并正在运行。错误: {e}")
        
        self._ensure_image_exists()
    
    def _ensure_image_exists(self):
        """确保 Docker 镜像存在，不存在则拉取"""
        try:
            self.client.images.get(self.image)
            logger.info(f"Docker 镜像已存在: {self.image}")
        except docker.errors.ImageNotFound:
            logger.info(f"正在拉取 Docker 镜像: {self.image}（首次运行可能需要几分钟）")
            try:
                self.client.images.pull(self.image)
                logger.info(f"Docker 镜像拉取成功: {self.image}")
            except Exception as e:
                logger.error(f"Docker 镜像拉取失败: {self.image}", error=str(e))
                raise Exception(f"无法拉取 Docker 镜像 {self.image}: {e}")
    
    def execute_python(self, code: str, timeout: Optional[int] = None) -> SandboxResult:
        """
        执行 Python 代码
        
        Args:
            code: Python 代码字符串
            timeout: 超时时间（秒），None 使用默认值
        
        Returns:
            SandboxResult 对象
        """
        return self.execute_code(code, language="python", timeout=timeout)
    
    def execute_code(self, code: str, language: str = "python", timeout: Optional[int] = None) -> SandboxResult:
        """
        执行代码（通用方法）
        
        Args:
            code: 代码字符串
            language: 语言类型 (python, bash, node 等)
            timeout: 超时时间（秒）
        
        Returns:
            SandboxResult 对象
        """
        timeout = timeout or self.timeout
        
        # 根据语言选择命令
        if language == "python":
            command = ["python", "-c", code]
        elif language == "bash" or language == "sh":
            command = ["bash", "-c", code]
        elif language == "node" or language == "javascript":
            command = ["node", "-e", code]
        else:
            return SandboxResult(
                success=False,
                output="",
                error=f"不支持的语言: {language}",
                exit_code=1
            )
        
        logger.info(f"执行代码", language=language, timeout=timeout)
        
        try:
            # 创建并运行容器
            container: Container = self.client.containers.run(
                image=self.image,
                command=command,
                detach=True,
                mem_limit=f"{self.memory_limit_mb}m",
                network_disabled=False,  # 允许网络访问（可根据需要禁用）
                remove=False,  # 执行完不立即删除，方便获取日志
            )
            
            try:
                # 等待容器执行完成
                result = container.wait(timeout=timeout)
                exit_code = result.get('StatusCode', -1)
                
                # 获取输出
                logs = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
                errors = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
                
                success = (exit_code == 0)
                
                logger.info(
                    f"代码执行完成",
                    success=success,
                    exit_code=exit_code,
                    output_length=len(logs),
                    error_length=len(errors)
                )
                
                return SandboxResult(
                    success=success,
                    output=logs,
                    error=errors,
                    exit_code=exit_code
                )
            
            finally:
                # 清理容器
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"容器清理失败", error=str(e))
        
        except docker.errors.ContainerError as e:
            logger.error("容器执行错误", error=str(e))
            return SandboxResult(
                success=False,
                output="",
                error=f"容器执行错误: {e}",
                exit_code=e.exit_status
            )
        
        except Exception as e:
            logger.error("沙箱执行失败", error=str(e))
            return SandboxResult(
                success=False,
                output="",
                error=f"执行失败: {e}",
                exit_code=-1
            )
    
    def cleanup(self):
        """清理资源"""
        try:
            self.client.close()
        except Exception:
            pass


def test_sandbox():
    """测试沙箱是否正常工作"""
    try:
        sandbox = DockerSandbox()
        
        # 测试 Python 代码执行
        print("测试 Python 代码执行:")
        code = """
print("Hello from Docker!")
for i in range(5):
    print(f"Count: {i}")
"""
        result = sandbox.execute_python(code)
        print(result)
        print()
        
        # 测试错误处理
        print("测试错误处理:")
        bad_code = "print(undefined_variable)"
        result = sandbox.execute_python(bad_code)
        print(result)
        print()
        
        sandbox.cleanup()
        print("✅ 沙箱测试通过")
        return True
    
    except Exception as e:
        print(f"❌ 沙箱测试失败: {e}")
        return False


if __name__ == "__main__":
    from core.utils import init_config, setup_logging
    
    # 初始化配置和日志
    init_config()
    setup_logging()
    
    # 运行测试
    test_sandbox()
