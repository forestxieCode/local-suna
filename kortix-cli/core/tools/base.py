"""工具基类和装饰器系统"""
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import inspect


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: Any
    error: Optional[str] = None
    
    def __str__(self):
        if self.success:
            return f"✅ 成功\n{self.output}"
        else:
            return f"❌ 失败\n{self.error}"


class Tool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._functions: Dict[str, Callable] = {}
    
    @abstractmethod
    def get_functions(self) -> List[Dict[str, Any]]:
        """
        返回工具的函数定义列表（OpenAI Function Calling 格式）
        
        Returns:
            函数定义列表，每个元素格式为：
            {
                "name": "function_name",
                "description": "功能描述",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        """
        pass
    
    def execute(self, function_name: str, **kwargs) -> ToolResult:
        """
        执行指定的工具函数
        
        Args:
            function_name: 函数名
            **kwargs: 函数参数
        
        Returns:
            ToolResult 对象
        """
        if function_name not in self._functions:
            return ToolResult(
                success=False,
                output="",
                error=f"函数 {function_name} 不存在"
            )
        
        try:
            result = self._functions[function_name](**kwargs)
            if isinstance(result, ToolResult):
                return result
            else:
                return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"执行失败: {str(e)}"
            )
    
    def register_function(self, name: str, func: Callable):
        """注册一个函数"""
        self._functions[name] = func


# 装饰器：用于标记工具函数
def tool_function(
    name: str,
    description: str,
    parameters: Optional[Dict[str, Any]] = None
):
    """
    工具函数装饰器
    
    Args:
        name: 函数名
        description: 函数描述
        parameters: 参数定义（OpenAI格式）
    """
    def decorator(func):
        func._is_tool_function = True
        func._function_name = name
        func._function_description = description
        func._function_parameters = parameters or {
            "type": "object",
            "properties": {},
            "required": []
        }
        return func
    return decorator
