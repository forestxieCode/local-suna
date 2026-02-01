"""阿里云百炼 LLM 接口"""
from typing import List, Dict, Any, Optional, Iterator
from dashscope import Generation
from dashscope.api_entities.dashscope_response import GenerationResponse
import dashscope
from core.utils.logger import get_logger
from core.utils.config import get_config

logger = get_logger(__name__)


class Message:
    """消息类 - 支持 Function Calling"""
    def __init__(self, role: str, content: str = "", tool_calls: Optional[List[Dict]] = None, 
                 tool_call_id: Optional[str] = None, name: Optional[str] = None):
        self.role = role  # 'user', 'assistant', 'system', 'tool'
        self.content = content
        self.tool_calls = tool_calls  # 用于 assistant 消息
        self.tool_call_id = tool_call_id  # 用于 tool 消息
        self.name = name  # 用于 tool 消息
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"role": self.role}
        
        if self.content:
            result["content"] = self.content
        
        # Function Calling 相关字段
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        
        if self.name:
            result["name"] = self.name
        
        return result


class LLM:
    """阿里云百炼 LLM 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        config = get_config()
        
        self.api_key = api_key or config.llm_api_key
        self.model = model or config.llm_model
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens
        
        if not self.api_key:
            raise ValueError("未设置 DASHSCOPE_API_KEY，请在配置文件或环境变量中设置")
        
        # 设置 API Key
        dashscope.api_key = self.api_key
        
        logger.info("LLM 初始化完成", model=self.model)
    
    def chat(
        self, 
        messages: List[Message],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大 token 数（可选，覆盖默认值）
        
        Returns:
            AI 回复内容
        """
        messages_dict = [msg.to_dict() for msg in messages]
        
        try:
            response = Generation.call(
                model=self.model,
                messages=messages_dict,
                result_format='message',
                stream=stream,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                incremental_output=stream
            )
            
            if stream:
                # 流式输出
                for chunk in response:
                    if chunk.status_code == 200:
                        content = chunk.output.choices[0].message.content
                        yield content
                    else:
                        error_msg = f"API 错误: {chunk.code} - {chunk.message}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                # ✅ 生成器函数不应该 return 值，会导致 StopIteration 错误
            else:
                # 非流式输出
                if response.status_code == 200:
                    return response.output.choices[0].message.content
                else:
                    error_msg = f"API 错误: {response.code} - {response.message}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
        
        except Exception as e:
            logger.error("LLM 调用失败", error=str(e))
            raise
    
    def chat_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        """
        流式对话（生成器）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Yields:
            每个 token 片段
        """
        messages_dict = [msg.to_dict() for msg in messages]
        
        try:
            response = Generation.call(
                model=self.model,
                messages=messages_dict,
                result_format='message',
                stream=True,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                incremental_output=True
            )
            
            for chunk in response:
                if chunk.status_code == 200:
                    content = chunk.output.choices[0].message.content
                    yield content
                else:
                    error_msg = f"API 错误: {chunk.code} - {chunk.message}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
        
        except Exception as e:
            logger.error("LLM 流式调用失败", error=str(e))
            raise


def test_llm():
    """测试 LLM 是否正常工作"""
    try:
        llm = LLM()
        messages = [Message("user", "你好，请用一句话介绍你自己")]
        
        print("测试非流式输出:")
        response = llm.chat(messages)
        print(f"回复: {response}\n")
        
        print("测试流式输出:")
        messages = [Message("user", "请数数 1 到 5")]
        for chunk in llm.chat_stream(messages):
            print(chunk, end='', flush=True)
        print("\n")
        
        print("✅ LLM 测试通过")
        return True
    
    except Exception as e:
        print(f"❌ LLM 测试失败: {e}")
        return False


if __name__ == "__main__":
    from core.utils import init_config, setup_logging
    
    # 初始化配置和日志
    init_config()
    setup_logging()
    
    # 运行测试
    test_llm()
