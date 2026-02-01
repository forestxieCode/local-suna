"""
DashScope (Aliyun Bailian) provider configuration.

Aliyun DashScope is China's leading LLM service, powered by Qwen models.
No VPN required, fast response times in China.

Official docs: https://help.aliyun.com/zh/dashscope/
"""

from typing import List, Optional
from ..models import Model, ModelProvider, ModelCapability, ModelPricing, ModelConfig
from .base import ProviderConfig


class DashScopeConfig(ProviderConfig):
    """Configuration for Aliyun DashScope (百炼) provider."""
    
    name = "DashScope"
    provider_id = ModelProvider.DASHSCOPE
    api_key_env = "DASHSCOPE_API_KEY"
    api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    @classmethod
    def get_models(cls) -> List[Model]:
        """
        Available Qwen models via DashScope.
        
        Model selection guide:
        - qwen-max: Best quality, slower, most expensive
        - qwen-plus: Balanced quality/speed/cost (recommended)
        - qwen-turbo: Fastest, cheapest, good for simple tasks
        - qwen-long: Ultra-long context (1M tokens)
        """
        return [
            # Qwen-Max - Flagship model
            Model(
                id="qwen-max",
                name="Qwen Max",
                provider=ModelProvider.DASHSCOPE,
                litellm_model_id="dashscope/qwen-max",
                context_window=30_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.VISION,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=20.0,  # ¥20/1M tokens
                    output_cost_per_million_tokens=60.0,  # ¥60/1M tokens
                ),
                tier_availability=["paid"],
                recommended=True,
                priority=100,
                config=ModelConfig(
                    api_base=cls.api_base,
                ),
            ),
            
            # Qwen-Plus - Recommended for most use cases
            Model(
                id="qwen-plus",
                name="Qwen Plus",
                provider=ModelProvider.DASHSCOPE,
                litellm_model_id="dashscope/qwen-plus",
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.VISION,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=4.0,  # ¥4/1M tokens
                    output_cost_per_million_tokens=12.0,  # ¥12/1M tokens
                ),
                tier_availability=["free", "paid"],
                recommended=True,
                priority=90,
                config=ModelConfig(
                    api_base=cls.api_base,
                ),
            ),
            
            # Qwen-Turbo - Fast and economical
            Model(
                id="qwen-turbo",
                name="Qwen Turbo",
                provider=ModelProvider.DASHSCOPE,
                litellm_model_id="dashscope/qwen-turbo",
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=2.0,  # ¥2/1M tokens
                    output_cost_per_million_tokens=6.0,  # ¥6/1M tokens
                ),
                tier_availability=["free", "paid"],
                recommended=True,
                priority=80,
                config=ModelConfig(
                    api_base=cls.api_base,
                ),
            ),
            
            # Qwen-Long - Ultra-long context
            Model(
                id="qwen-long",
                name="Qwen Long (1M context)",
                provider=ModelProvider.DASHSCOPE,
                litellm_model_id="dashscope/qwen-long",
                context_window=1_000_000,
                capabilities=[
                    ModelCapability.CHAT,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=0.5,  # ¥0.5/1M tokens
                    output_cost_per_million_tokens=2.0,  # ¥2/1M tokens
                ),
                tier_availability=["paid"],
                priority=70,
                config=ModelConfig(
                    api_base=cls.api_base,
                ),
            ),
            
            # Qwen2.5-72B - Open source deployment option
            Model(
                id="qwen2.5-72b-instruct",
                name="Qwen 2.5 72B",
                provider=ModelProvider.DASHSCOPE,
                litellm_model_id="dashscope/qwen2.5-72b-instruct",
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=3.0,
                    output_cost_per_million_tokens=9.0,
                ),
                tier_availability=["paid"],
                priority=60,
                config=ModelConfig(
                    api_base=cls.api_base,
                ),
            ),
            
            # Qwen2.5-Coder - Specialized for coding
            Model(
                id="qwen2.5-coder-32b-instruct",
                name="Qwen 2.5 Coder 32B",
                provider=ModelProvider.DASHSCOPE,
                litellm_model_id="dashscope/qwen2.5-coder-32b-instruct",
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=2.0,
                    output_cost_per_million_tokens=6.0,
                ),
                tier_availability=["paid"],
                priority=85,
                config=ModelConfig(
                    api_base=cls.api_base,
                ),
            ),
        ]
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if DashScope API key is configured."""
        import os
        return bool(os.getenv(cls.api_key_env))
    
    @classmethod
    def get_setup_instructions(cls) -> str:
        """Return setup instructions for DashScope."""
        return """
        To use Aliyun DashScope (百炼):
        
        1. Visit https://dashscope.console.aliyun.com/
        2. Sign up / Login with Aliyun account
        3. Create an API key
        4. Add to your .env file:
           DASHSCOPE_API_KEY=sk-your-api-key-here
        
        Features:
        - No VPN required (China-based)
        - Fast response times
        - Competitive pricing
        - Supports vision, function calling
        - Free tier available
        """
