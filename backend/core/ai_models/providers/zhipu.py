"""
Zhipu AI (智谱AI) provider configuration.

Zhipu AI's GLM models are popular Chinese LLMs.

Official docs: https://open.bigmodel.cn/
"""

from typing import List
from ..models import Model, ModelProvider, ModelCapability, ModelPricing, ModelConfig
from .base import ProviderConfig


class ZhipuAIConfig(ProviderConfig):
    """Configuration for Zhipu AI (智谱AI) provider."""
    
    name = "ZhipuAI"
    provider_id = ModelProvider.ZHIPU
    api_key_env = "ZHIPU_API_KEY"
    api_base = "https://open.bigmodel.cn/api/paas/v4"
    
    @classmethod
    def get_models(cls) -> List[Model]:
        """Available GLM models."""
        return [
            # GLM-4 - Flagship model
            Model(
                id="glm-4",
                name="GLM-4",
                provider=ModelProvider.ZHIPU,
                litellm_model_id="zhipu/glm-4",
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.VISION,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=100.0,  # ¥100/1M tokens
                    output_cost_per_million_tokens=100.0,
                ),
                tier_availability=["paid"],
                recommended=True,
                priority=100,
            ),
            
            # GLM-4 Flash - Fast and economical
            Model(
                id="glm-4-flash",
                name="GLM-4 Flash",
                provider=ModelProvider.ZHIPU,
                litellm_model_id="zhipu/glm-4-flash",
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=1.0,  # ¥1/1M tokens
                    output_cost_per_million_tokens=1.0,
                ),
                tier_availability=["free", "paid"],
                recommended=True,
                priority=90,
            ),
            
            # GLM-4V - Vision model
            Model(
                id="glm-4v",
                name="GLM-4V (Vision)",
                provider=ModelProvider.ZHIPU,
                litellm_model_id="zhipu/glm-4v",
                context_window=8_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=50.0,
                    output_cost_per_million_tokens=50.0,
                ),
                tier_availability=["paid"],
                priority=85,
            ),
        ]
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if Zhipu API key is configured."""
        import os
        return bool(os.getenv(cls.api_key_env))
    
    @classmethod
    def get_setup_instructions(cls) -> str:
        """Return setup instructions."""
        return """
        To use Zhipu AI (智谱AI):
        
        1. Visit https://open.bigmodel.cn/
        2. Sign up / Login
        3. Create an API key
        4. Add to .env:
           ZHIPU_API_KEY=your-api-key-here
        
        Features:
        - China-based (no VPN)
        - Competitive pricing
        - Vision support
        - Free tier available
        """
