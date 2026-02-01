"""Shell 命令执行工具"""
from typing import List
import subprocess
from core.tools.base import Tool, ToolResult
from core.utils.logger import get_logger

logger = get_logger(__name__)


class ShellTool(Tool):
    """Shell 命令执行工具"""
    
    def __init__(self, workspace_dir: str = "./workspace"):
        super().__init__("shell", "执行 Shell 命令")
        self.workspace_dir = workspace_dir
        
        # 注册函数
        self.register_function("execute", self.execute_command)
    
    def get_functions(self) -> List[dict]:
        return [
            {
                "name": "execute",
                "description": "在workspace目录中执行Shell命令（如git、npm、pip等）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的命令"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间（秒），默认60"
                        }
                    },
                    "required": ["command"]
                }
            }
        ]
    
    def execute_command(self, command: str, timeout: int = 60) -> ToolResult:
        """执行Shell命令"""
        try:
            logger.info("执行命令", command=command)
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout if result.stdout else result.stderr
            
            if result.returncode == 0:
                logger.info("命令执行成功", command=command)
                return ToolResult(success=True, output=output)
            else:
                logger.warning("命令执行失败", command=command, code=result.returncode)
                return ToolResult(
                    success=False,
                    output=output,
                    error=f"命令返回码: {result.returncode}"
                )
        
        except subprocess.TimeoutExpired:
            logger.error("命令超时", command=command, timeout=timeout)
            return ToolResult(
                success=False,
                output="",
                error=f"命令执行超时（{timeout}秒）"
            )
        
        except Exception as e:
            logger.error("命令执行失败", command=command, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
