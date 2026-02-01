"""Web 搜索工具 - 使用 Tavily API"""
from typing import List, Optional
from core.tools.base import Tool, ToolResult
from core.utils.logger import get_logger
from core.utils.config import get_config
import os

logger = get_logger(__name__)


class WebSearchTool(Tool):
    """Web 搜索工具（使用 Tavily）"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("web_search", "网络搜索工具")
        
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        
        # 只在有 API Key 时导入
        if self.api_key:
            try:
                from tavily import TavilyClient
                self.client = TavilyClient(api_key=self.api_key)
                self.enabled = True
                logger.info("Web搜索工具已启用")
            except ImportError:
                self.enabled = False
                logger.warning("Tavily未安装，Web搜索功能不可用")
        else:
            self.enabled = False
            logger.info("未配置TAVILY_API_KEY，Web搜索功能禁用")
        
        # 注册函数
        self.register_function("search", self.search)
        self.register_function("search_news", self.search_news)
    
    def get_functions(self) -> List[dict]:
        if not self.enabled:
            return []
        
        return [
            {
                "name": "search",
                "description": "在网络上搜索信息，获取最新的资料和数据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询词"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大结果数（默认5）"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_news",
                "description": "搜索最新新闻",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "新闻查询词"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大结果数（默认5）"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    def search(self, query: str, max_results: int = 5) -> ToolResult:
        """搜索网络"""
        if not self.enabled:
            return ToolResult(
                success=False,
                output="",
                error="Web搜索未启用。请设置 TAVILY_API_KEY 环境变量"
            )
        
        try:
            logger.info("执行网络搜索", query=query)
            
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            results = response.get("results", [])
            if not results:
                return ToolResult(success=True, output="未找到相关结果")
            
            # 格式化结果
            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "无标题")
                url = result.get("url", "")
                snippet = result.get("content", "")[:200]
                
                formatted.append(f"{i}. **{title}**\n   {snippet}...\n   链接: {url}")
            
            output = "\n\n".join(formatted)
            logger.info("搜索完成", results=len(results))
            return ToolResult(success=True, output=output)
        
        except Exception as e:
            logger.error("搜索失败", query=query, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
    
    def search_news(self, query: str, max_results: int = 5) -> ToolResult:
        """搜索新闻"""
        if not self.enabled:
            return ToolResult(
                success=False,
                output="",
                error="Web搜索未启用"
            )
        
        try:
            logger.info("执行新闻搜索", query=query)
            
            response = self.client.search(
                query=query,
                max_results=max_results,
                topic="news"
            )
            
            results = response.get("results", [])
            if not results:
                return ToolResult(success=True, output="未找到相关新闻")
            
            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "")
                url = result.get("url", "")
                snippet = result.get("content", "")[:200]
                
                formatted.append(f"{i}. **{title}**\n   {snippet}...\n   链接: {url}")
            
            output = "\n\n".join(formatted)
            return ToolResult(success=True, output=output)
        
        except Exception as e:
            logger.error("新闻搜索失败", query=query, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
