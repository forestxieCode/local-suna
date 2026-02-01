"""AI Agent 核心 - 对话和工具调用管理"""
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
from pathlib import Path

from core.llm import LLM, Message
from core.sandbox import DockerSandbox, SandboxResult
from core.utils.logger import get_logger
from core.utils.config import get_config

logger = get_logger(__name__)


class Tool:
    """工具基类"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> str:
        """执行工具，返回结果字符串"""
        raise NotImplementedError


class CodeExecutorTool(Tool):
    """代码执行工具"""
    def __init__(self, sandbox: DockerSandbox):
        super().__init__(
            name="execute_code",
            description="执行 Python 代码。用于数据计算、文件处理等任务。"
        )
        self.sandbox = sandbox
    
    def execute(self, code: str, language: str = "python") -> str:
        """执行代码"""
        logger.info(f"执行代码", language=language, code_length=len(code))
        
        result = self.sandbox.execute_code(code, language=language)
        
        if result.success:
            return f"✅ 代码执行成功\n\n输出:\n{result.output}"
        else:
            return f"❌ 代码执行失败\n\n错误:\n{result.error}"


class Agent:
    """AI Agent - 对话和工具调用管理"""
    
    def __init__(self):
        config = get_config()
        
        self.llm = LLM()
        self.sandbox = DockerSandbox() if config.sandbox_enabled else None
        
        # 对话历史
        self.messages: List[Message] = []
        self.max_messages = config.history_max_messages
        
        # 工具
        self.tools: Dict[str, Tool] = {}
        if self.sandbox:
            self.tools["execute_code"] = CodeExecutorTool(self.sandbox)
        
        # 系统提示词
        self.system_prompt = self._build_system_prompt()
        self.messages.append(Message("system", self.system_prompt))
        
        logger.info("Agent 初始化完成", tools=list(self.tools.keys()))
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        prompt = """你是 Kortix AI Agent，一个智能助手。

你的能力：
1. 对话交流 - 回答问题、提供建议
2. 代码执行 - 可以编写和运行 Python 代码来完成任务

当用户需要你执行代码时，请使用以下格式：

```python
# 你的 Python 代码
print("Hello")
```

你可以执行代码来：
- 进行数学计算
- 处理数据
- 生成图表
- 文件操作
- 等等

请用中文回复用户。保持友好和专业。
"""
        
        if self.sandbox:
            prompt += "\n⚠️ 代码会在隔离的 Docker 容器中执行，确保安全。"
        
        return prompt
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """提取 Markdown 代码块"""
        # 匹配 ```language\ncode\n```
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        code_blocks = []
        for language, code in matches:
            code_blocks.append({
                "language": language or "python",
                "code": code.strip()
            })
        
        return code_blocks
    
    def _should_execute_code(self, response: str) -> bool:
        """判断是否需要执行代码"""
        # 检查是否包含代码块
        code_blocks = self._extract_code_blocks(response)
        return len(code_blocks) > 0
    
    def chat(self, user_input: str, stream: bool = True) -> str:
        """
        与 Agent 对话
        
        Args:
            user_input: 用户输入
            stream: 是否流式输出
        
        Returns:
            Agent 的回复
        """
        # 添加用户消息
        self.messages.append(Message("user", user_input))
        
        # 限制历史消息数量（保留系统消息）
        if len(self.messages) > self.max_messages:
            system_msg = self.messages[0]
            self.messages = [system_msg] + self.messages[-(self.max_messages-1):]
        
        logger.info("用户输入", input=user_input, message_count=len(self.messages))
        
        # 调用 LLM
        if stream:
            response = ""
            for chunk in self.llm.chat_stream(self.messages):
                response += chunk
                yield chunk
            
            # 检查是否需要执行代码
            if self._should_execute_code(response) and self.sandbox:
                # 执行代码
                code_blocks = self._extract_code_blocks(response)
                for block in code_blocks:
                    language = block["language"]
                    code = block["code"]
                    
                    yield f"\n\n[执行 {language} 代码...]\n"
                    
                    tool = self.tools.get("execute_code")
                    if tool:
                        result = tool.execute(code=code, language=language)
                        yield result
                        response += f"\n\n{result}"
            
            # 添加助手回复到历史
            self.messages.append(Message("assistant", response))
            return response
        else:
            response = self.llm.chat(self.messages)
            
            # 检查是否需要执行代码
            if self._should_execute_code(response) and self.sandbox:
                code_blocks = self._extract_code_blocks(response)
                for block in code_blocks:
                    tool = self.tools.get("execute_code")
                    if tool:
                        result = tool.execute(code=block["code"], language=block["language"])
                        response += f"\n\n{result}"
            
            # 添加助手回复到历史
            self.messages.append(Message("assistant", response))
            return response
    
    def reset(self):
        """重置对话历史"""
        self.messages = [Message("system", self.system_prompt)]
        logger.info("对话历史已重置")
    
    def save_history(self, filepath: Optional[str] = None):
        """保存对话历史到文件"""
        config = get_config()
        
        if not config.history_save_to_file:
            return
        
        if not filepath:
            # 自动生成文件名
            history_dir = Path(config.history_file_path)
            history_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = history_dir / f"conversation_{timestamp}.json"
        
        # 转换为可序列化格式
        history_data = {
            "timestamp": datetime.now().isoformat(),
            "messages": [{"role": msg.role, "content": msg.content} for msg in self.messages]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"对话历史已保存", filepath=str(filepath))
    
    def load_history(self, filepath: str):
        """从文件加载对话历史"""
        with open(filepath, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        self.messages = [
            Message(msg["role"], msg["content"]) 
            for msg in history_data["messages"]
        ]
        
        logger.info(f"对话历史已加载", filepath=filepath, message_count=len(self.messages))
    
    def cleanup(self):
        """清理资源"""
        if self.sandbox:
            self.sandbox.cleanup()


def test_agent():
    """测试 Agent 功能"""
    try:
        agent = Agent()
        
        print("=" * 60)
        print("测试 1: 简单对话")
        print("=" * 60)
        user_input = "你好，请介绍一下你自己"
        print(f"用户: {user_input}\n")
        print("Agent: ", end='')
        for chunk in agent.chat(user_input):
            print(chunk, end='', flush=True)
        print("\n")
        
        print("=" * 60)
        print("测试 2: 代码执行")
        print("=" * 60)
        user_input = "帮我写一个 Python 代码，计算斐波那契数列的前 10 项"
        print(f"用户: {user_input}\n")
        print("Agent: ", end='')
        for chunk in agent.chat(user_input):
            print(chunk, end='', flush=True)
        print("\n")
        
        # 保存历史
        agent.save_history()
        
        agent.cleanup()
        print("✅ Agent 测试通过")
        return True
    
    except Exception as e:
        print(f"❌ Agent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    from core.utils import init_config, setup_logging
    
    # 初始化
    init_config()
    setup_logging()
    
    # 运行测试
    test_agent()
