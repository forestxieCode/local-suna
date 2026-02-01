"""AI Agent 核心 - 增强版，支持完整工具系统和 Function Calling"""
from typing import List, Dict, Any, Optional, Iterator
import json
import re
from datetime import datetime
from pathlib import Path

from core.llm import LLM, Message
from core.sandbox import DockerSandbox
from core.tools import (
    ToolRegistry,
    FileManagerTool,
    WebSearchTool,
    ShellTool,
    CalculatorTool,
    ToolResult
)
from core.utils.logger import get_logger
from core.utils.config import get_config

logger = get_logger(__name__)


class CodeExecutorTool:
    """代码执行工具包装器"""
    def __init__(self, sandbox: DockerSandbox):
        self.sandbox = sandbox
        self.name = "code_executor"
        self.description = "执行Python代码"
    
    def get_functions(self):
        return [{
            "name": "execute_python",
            "description": "在Docker沙箱中执行Python代码，用于数据计算、文件处理等",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的Python代码"
                    }
                },
                "required": ["code"]
            }
        }]
    
    def execute(self, function_name: str, **kwargs):
        if function_name == "execute_python":
            code = kwargs.get("code", "")
            result = self.sandbox.execute_python(code)
            return ToolResult(
                success=result.success,
                output=result.output,
                error=result.error
            )
        return ToolResult(success=False, output="", error="未知函数")


class Agent:
    """AI Agent - 增强版，支持完整工具系统"""
    
    def __init__(self):
        config = get_config()
        
        # 初始化 LLM
        self.llm = LLM()
        
        # 初始化工具注册表
        self.tool_registry = ToolRegistry()
        
        # 注册所有工具
        self._register_tools(config)
        
        # 对话历史
        self.messages: List[Message] = []
        self.max_messages = config.history_max_messages
        
        # 系统提示词
        self.system_prompt = self._build_system_prompt()
        self.messages.append(Message("system", self.system_prompt))
        
        # 是否启用 Function Calling
        self.enable_function_calling = config.get('llm.enable_function_calling', True)
        
        logger.info(
            "Agent 初始化完成",
            tools=self.tool_registry.list_tools(),
            function_calling=self.enable_function_calling
        )
    
    def _register_tools(self, config):
        """注册所有工具"""
        # 文件管理工具
        if config.get('tools.file_manager.enabled', True):
            workspace = config.get('tools.file_manager.workspace_dir', './workspace')
            self.tool_registry.register(FileManagerTool(workspace))
            logger.info("已注册文件管理工具")
        
        # Web 搜索工具
        if config.get('tools.web_search.enabled', True):
            api_key = config.get('tools.web_search.api_key')
            self.tool_registry.register(WebSearchTool(api_key))
            logger.info("已注册Web搜索工具")
        
        # Shell 工具
        if config.get('tools.shell.enabled', True):
            workspace = config.get('tools.file_manager.workspace_dir', './workspace')
            self.tool_registry.register(ShellTool(workspace))
            logger.info("已注册Shell工具")
        
        # 计算器工具
        if config.get('tools.calculator.enabled', True):
            self.tool_registry.register(CalculatorTool())
            logger.info("已注册计算器工具")
        
        # 代码执行工具
        if config.get('tools.code_executor.enabled', True) and config.sandbox_enabled:
            sandbox = DockerSandbox()
            code_tool = CodeExecutorTool(sandbox)
            self.tool_registry.register(code_tool)
            logger.info("已注册代码执行工具")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_info = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get_tool(tool_name)
            tools_info.append(f"- **{tool.name}**: {tool.description}")
        
        tools_desc = "\n".join(tools_info)
        
        prompt = f"""你是 Kortix AI Agent，一个强大的智能助手。

你的能力：
1. **对话交流** - 回答问题、提供建议
2. **工具调用** - 使用以下工具完成任务：

{tools_desc}

**工具使用指南：**
- 当用户的请求需要使用工具时，你会自动调用合适的工具
- 每次可以调用多个工具来完成复杂任务
- 工具执行后，你会看到结果并基于结果回复用户

**重要规则：**
- 使用中文回复用户
- 保持友好和专业的态度
- 如果不确定，可以询问用户更多细节
- 在执行重要操作前，向用户确认

现在，让我们开始帮助用户吧！
"""
        return prompt
    
    def _get_tool_functions(self) -> List[Dict[str, Any]]:
        """获取所有工具的函数定义（用于 Function Calling）"""
        return self.tool_registry.get_all_functions()
    
    def _call_llm_with_tools(self, messages: List[Message]) -> Dict[str, Any]:
        """调用 LLM（带工具支持）"""
        # 准备消息 - 使用 to_dict() 保留所有字段（tool_calls, tool_call_id, name 等）
        messages_dict = [msg.to_dict() for msg in messages]
        
        # 准备工具定义
        tools = []
        if self.enable_function_calling:
            functions = self._get_tool_functions()
            tools = [{"type": "function", "function": func} for func in functions]
        
        # 调用百炼API（使用原生API以支持tools参数）
        from dashscope import Generation
        import dashscope
        
        config = get_config()
        dashscope.api_key = config.llm_api_key
        
        response = Generation.call(
            model=config.llm_model,
            messages=messages_dict,
            result_format='message',
            tools=tools if tools else None,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens
        )
        
        if response.status_code != 200:
            raise Exception(f"LLM调用失败: {response.message}")
        
        return response.output.choices[0].message
    
    def chat(self, user_input: str, stream: bool = True) -> Iterator[str]:
        """
        与 Agent 对话
        
        Args:
            user_input: 用户输入
            stream: 是否流式输出
        
        Yields:
            Agent 的回复片段
        """
        # 添加用户消息
        self.messages.append(Message("user", user_input))
        
        # 限制历史消息数量
        if len(self.messages) > self.max_messages:
            system_msg = self.messages[0]
            self.messages = [system_msg] + self.messages[-(self.max_messages-1):]
        
        logger.info("用户输入", input=user_input, message_count=len(self.messages))
        
        # 多轮工具调用循环
        max_iterations = 5
        iteration = 0
        full_response = ""
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # 调用 LLM
                response_message = self._call_llm_with_tools(self.messages)
                
                # 检查是否需要调用工具
                tool_calls = response_message.get('tool_calls', [])
                
                if not tool_calls:
                    # 没有工具调用，直接返回回复
                    content = response_message.get('content', '')
                    
                    if stream:
                        # 模拟流式输出
                        for char in content:
                            yield char
                            full_response += char
                    else:
                        full_response = content
                        yield content
                    
                    # 添加助手回复到历史
                    self.messages.append(Message("assistant", full_response))
                    break
                
                else:
                    # 有工具调用
                    assistant_message_content = response_message.get('content', '')
                    if assistant_message_content:
                        full_response += assistant_message_content
                        if stream:
                            yield assistant_message_content
                    
                    # 添加助手消息（包含tool_calls）
                    self.messages.append(Message(
                        role="assistant",
                        content=assistant_message_content,
                        tool_calls=tool_calls
                    ))
                    
                    # 执行所有工具调用
                    for tool_call in tool_calls:
                        function_name = tool_call['function']['name']
                        arguments = json.loads(tool_call['function']['arguments'])
                        tool_call_id = tool_call['id']
                        
                        logger.info("调用工具", function=function_name, args=arguments)
                        
                        # 通知用户
                        tool_msg = f"\n\n🔧 [使用工具: {function_name}]\n"
                        full_response += tool_msg
                        if stream:
                            yield tool_msg
                        
                        # 执行工具
                        result = self.tool_registry.execute(function_name, **arguments)
                        
                        # 显示工具结果
                        result_text = str(result)
                        if len(result_text) > 500:
                            result_text = result_text[:500] + "...\n(输出已截断)"
                        
                        result_msg = f"{result_text}\n"
                        full_response += result_msg
                        if stream:
                            yield result_msg
                        
                        # 添加工具结果到消息历史
                        self.messages.append(Message(
                            role="tool",
                            content=result.output if result.success else result.error,
                            tool_call_id=tool_call_id,
                            name=function_name
                        ))
                    
                    # 继续下一轮对话（让LLM基于工具结果回复）
                    continue
            
            except Exception as e:
                error_msg = f"\n\n❌ 错误: {str(e)}\n"
                logger.error("对话失败", error=str(e))
                full_response += error_msg
                yield error_msg
                break
        
        if iteration >= max_iterations:
            warning = "\n\n⚠️ 达到最大工具调用次数限制"
            full_response += warning
            yield warning
    
    def reset(self):
        """重置对话历史"""
        self.messages = [Message("system", self.system_prompt)]
        logger.info("对话历史已重置")
    
    def save_history(self, filepath: Optional[str] = None):
        """保存对话历史"""
        config = get_config()
        
        if not config.history_save_to_file:
            return
        
        if not filepath:
            history_dir = Path(config.history_file_path)
            history_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = history_dir / f"conversation_{timestamp}.json"
        
        history_data = {
            "timestamp": datetime.now().isoformat(),
            "messages": [{"role": msg.role, "content": msg.content} for msg in self.messages]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"对话历史已保存", filepath=str(filepath))
    
    def load_history(self, filepath: str):
        """加载对话历史"""
        with open(filepath, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        self.messages = [
            Message(msg["role"], msg["content"]) 
            for msg in history_data["messages"]
        ]
        
        logger.info(f"对话历史已加载", filepath=filepath, message_count=len(self.messages))
    
    def cleanup(self):
        """清理资源"""
        # 清理 Docker 沙箱
        code_tool = self.tool_registry.get_tool("code_executor")
        if code_tool and hasattr(code_tool, 'sandbox'):
            code_tool.sandbox.cleanup()


def test_agent():
    """测试增强版 Agent"""
    try:
        from core.utils import init_config, setup_logging
        
        # 初始化
        init_config()
        setup_logging()
        
        agent = Agent()
        
        print("=" * 60)
        print("测试 1: 简单对话")
        print("=" * 60)
        user_input = "你好，请介绍一下你的能力"
        print(f"用户: {user_input}\n")
        print("Agent: ", end='')
        for chunk in agent.chat(user_input):
            print(chunk, end='', flush=True)
        print("\n")
        
        print("=" * 60)
        print("测试 2: 使用计算器")
        print("=" * 60)
        user_input = "帮我计算 123 * 456 + 789"
        print(f"用户: {user_input}\n")
        print("Agent: ", end='')
        for chunk in agent.chat(user_input):
            print(chunk, end='', flush=True)
        print("\n")
        
        print("=" * 60)
        print("测试 3: 文件操作")
        print("=" * 60)
        user_input = "创建一个文件test.txt，内容是'Hello, World!'"
        print(f"用户: {user_input}\n")
        print("Agent: ", end='')
        for chunk in agent.chat(user_input):
            print(chunk, end='', flush=True)
        print("\n")
        
        print("=" * 60)
        print("测试 4: 代码执行")
        print("=" * 60)
        user_input = "写一个Python代码，生成10个随机数并计算平均值"
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
    test_agent()
