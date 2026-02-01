"""文件管理工具 - 读写编辑搜索文件"""
from typing import Optional, List
import os
from pathlib import Path
import re
from core.tools.base import Tool, ToolResult
from core.utils.logger import get_logger

logger = get_logger(__name__)


class FileManagerTool(Tool):
    """文件管理工具"""
    
    def __init__(self, workspace_dir: str = "./workspace"):
        super().__init__("file_manager", "文件读写、编辑、搜索")
        
        self.workspace_dir = Path(workspace_dir).absolute()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # 注册函数
        self.register_function("read_file", self.read_file)
        self.register_function("write_file", self.write_file)
        self.register_function("edit_file", self.edit_file)
        self.register_function("list_files", self.list_files)
        self.register_function("search_in_files", self.search_in_files)
        self.register_function("delete_file", self.delete_file)
    
    def get_functions(self) -> List[dict]:
        return [
            {
                "name": "read_file",
                "description": "读取文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于workspace）"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "写入文件内容（会覆盖现有文件）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "edit_file",
                "description": "编辑文件（替换指定文本）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "old_text": {
                            "type": "string",
                            "description": "要替换的文本"
                        },
                        "new_text": {
                            "type": "string",
                            "description": "新文本"
                        }
                    },
                    "required": ["path", "old_text", "new_text"]
                }
            },
            {
                "name": "list_files",
                "description": "列出目录中的文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "目录路径（默认为根目录）"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "是否递归列出子目录"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_in_files",
                "description": "在文件中搜索文本",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "搜索模式（正则表达式）"
                        },
                        "path": {
                            "type": "string",
                            "description": "搜索路径"
                        }
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "delete_file",
                "description": "删除文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]
    
    def _get_full_path(self, path: str) -> Path:
        """获取完整路径"""
        full_path = (self.workspace_dir / path).resolve()
        # 安全检查：确保路径在workspace内
        if not str(full_path).startswith(str(self.workspace_dir)):
            raise ValueError("路径必须在workspace目录内")
        return full_path
    
    def read_file(self, path: str) -> ToolResult:
        """读取文件"""
        try:
            full_path = self._get_full_path(path)
            if not full_path.exists():
                return ToolResult(success=False, output="", error=f"文件不存在: {path}")
            
            content = full_path.read_text(encoding='utf-8')
            logger.info("读取文件", path=path, size=len(content))
            return ToolResult(success=True, output=content)
        
        except Exception as e:
            logger.error("读取文件失败", path=path, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
    
    def write_file(self, path: str, content: str) -> ToolResult:
        """写入文件"""
        try:
            full_path = self._get_full_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            full_path.write_text(content, encoding='utf-8')
            logger.info("写入文件", path=path, size=len(content))
            return ToolResult(success=True, output=f"已写入 {len(content)} 字节到 {path}")
        
        except Exception as e:
            logger.error("写入文件失败", path=path, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
    
    def edit_file(self, path: str, old_text: str, new_text: str) -> ToolResult:
        """编辑文件"""
        try:
            full_path = self._get_full_path(path)
            if not full_path.exists():
                return ToolResult(success=False, output="", error=f"文件不存在: {path}")
            
            content = full_path.read_text(encoding='utf-8')
            
            if old_text not in content:
                return ToolResult(success=False, output="", error="未找到要替换的文本")
            
            new_content = content.replace(old_text, new_text, 1)
            full_path.write_text(new_content, encoding='utf-8')
            
            logger.info("编辑文件", path=path)
            return ToolResult(success=True, output=f"已替换文本: {path}")
        
        except Exception as e:
            logger.error("编辑文件失败", path=path, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
    
    def list_files(self, path: str = ".", recursive: bool = False) -> ToolResult:
        """列出文件"""
        try:
            full_path = self._get_full_path(path)
            if not full_path.exists():
                return ToolResult(success=False, output="", error=f"目录不存在: {path}")
            
            if not full_path.is_dir():
                return ToolResult(success=False, output="", error=f"不是目录: {path}")
            
            files = []
            if recursive:
                for item in full_path.rglob("*"):
                    rel_path = item.relative_to(self.workspace_dir)
                    files.append(str(rel_path))
            else:
                for item in full_path.iterdir():
                    rel_path = item.relative_to(self.workspace_dir)
                    files.append(str(rel_path))
            
            logger.info("列出文件", path=path, count=len(files))
            return ToolResult(success=True, output="\n".join(sorted(files)))
        
        except Exception as e:
            logger.error("列出文件失败", path=path, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
    
    def search_in_files(self, pattern: str, path: str = ".") -> ToolResult:
        """搜索文件内容"""
        try:
            full_path = self._get_full_path(path)
            regex = re.compile(pattern)
            results = []
            
            if full_path.is_file():
                files = [full_path]
            else:
                files = list(full_path.rglob("*"))
            
            for file in files:
                if file.is_file():
                    try:
                        content = file.read_text(encoding='utf-8')
                        matches = regex.findall(content)
                        if matches:
                            rel_path = file.relative_to(self.workspace_dir)
                            results.append(f"{rel_path}: {len(matches)} 个匹配")
                    except:
                        pass
            
            logger.info("搜索文件", pattern=pattern, matches=len(results))
            return ToolResult(success=True, output="\n".join(results) if results else "未找到匹配")
        
        except Exception as e:
            logger.error("搜索失败", pattern=pattern, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
    
    def delete_file(self, path: str) -> ToolResult:
        """删除文件"""
        try:
            full_path = self._get_full_path(path)
            if not full_path.exists():
                return ToolResult(success=False, output="", error=f"文件不存在: {path}")
            
            full_path.unlink()
            logger.info("删除文件", path=path)
            return ToolResult(success=True, output=f"已删除: {path}")
        
        except Exception as e:
            logger.error("删除文件失败", path=path, error=str(e))
            return ToolResult(success=False, output="", error=str(e))
