"""工具注册系统"""
from typing import Dict, List, Any, Optional
from core.tools.base import Tool, ToolResult
from core.utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._function_map: Dict[str, str] = {}  # function_name -> tool_name
    
    def register(self, tool: Tool):
        """注册一个工具"""
        self.tools[tool.name] = tool
        
        # 注册工具的所有函数
        for func_def in tool.get_functions():
            func_name = func_def["name"]
            self._function_map[func_name] = tool.name
        
        logger.info(f"注册工具", tool=tool.name, functions=len(tool.get_functions()))
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def get_all_functions(self) -> List[Dict[str, Any]]:
        """获取所有工具的函数定义"""
        functions = []
        for tool in self.tools.values():
            functions.extend(tool.get_functions())
        return functions
    
    def execute(self, function_name: str, **kwargs) -> ToolResult:
        """执行工具函数"""
        tool_name = self._function_map.get(function_name)
        if not tool_name:
            return ToolResult(
                success=False,
                output="",
                error=f"函数 {function_name} 未注册"
            )
        
        tool = self.tools[tool_name]
        return tool.execute(function_name, **kwargs)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())
    
    def list_functions(self) -> List[str]:
        """列出所有函数"""
        return list(self._function_map.keys())
