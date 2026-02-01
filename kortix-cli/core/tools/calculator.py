"""计算器和实用工具"""
from typing import List
import math
import re
from datetime import datetime
from core.tools.base import Tool, ToolResult
from core.utils.logger import get_logger

logger = get_logger(__name__)


class CalculatorTool(Tool):
    """计算器和实用工具"""
    
    def __init__(self):
        super().__init__("calculator", "数学计算和实用工具")
        
        # 注册函数
        self.register_function("calculate", self.calculate)
        self.register_function("get_current_time", self.get_current_time)
    
    def get_functions(self) -> List[dict]:
        return [
            {
                "name": "calculate",
                "description": "执行数学计算（支持基本运算、三角函数、对数等）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '2 + 3 * 4' 或 'sin(pi/2)'"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "get_current_time",
                "description": "获取当前时间",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "时间格式（默认: '%Y-%m-%d %H:%M:%S'）"
                        }
                    },
                    "required": []
                }
            }
        ]
    
    def calculate(self, expression: str) -> ToolResult:
        """计算数学表达式"""
        try:
            # 安全的数学环境
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                # 数学函数
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "floor": math.floor,
                "ceil": math.ceil,
                # 常量
                "pi": math.pi,
                "e": math.e,
            }
            
            # 清理表达式（只保留安全字符）
            cleaned = re.sub(r'[^0-9+\-*/().,\sa-z]', '', expression.lower())
            
            # 计算
            result = eval(cleaned, {"__builtins__": {}}, safe_dict)
            
            logger.info("计算完成", expression=expression, result=result)
            return ToolResult(success=True, output=f"{expression} = {result}")
        
        except Exception as e:
            logger.error("计算失败", expression=expression, error=str(e))
            return ToolResult(success=False, output="", error=f"计算错误: {str(e)}")
    
    def get_current_time(self, format: str = "%Y-%m-%d %H:%M:%S") -> ToolResult:
        """获取当前时间"""
        try:
            current_time = datetime.now().strftime(format)
            return ToolResult(success=True, output=current_time)
        
        except Exception as e:
            logger.error("获取时间失败", error=str(e))
            return ToolResult(success=False, output="", error=str(e))
