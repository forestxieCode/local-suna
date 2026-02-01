"""
Ollama provider configuration for local LLM deployment.

Ollama enables running LLMs locally without internet connection.
Perfect for privacy, offline usage, and development.

Official docs: https://ollama.ai/
"""

from typing import List, Optional
from ..models import Model, ModelProvider, ModelCapability, ModelPricing, ModelConfig
from .base import ProviderConfig


class OllamaConfig(ProviderConfig):
    """Configuration for Ollama local LLM provider."""
    
    name = "Ollama"
    provider_id = ModelProvider.OLLAMA
    api_key_env = None  # No API key needed for local
    api_base_env = "OLLAMA_BASE_URL"
    default_api_base = "http://localhost:11434"
    
    @classmethod
    def get_models(cls) -> List[Model]:
        """
        Popular Ollama models.
        
        Users can run any model from https://ollama.ai/library
        """
        return [
            # Qwen 2.5 - Alibaba's open source models
            Model(
                id="qwen2.5:7b",
                name="Qwen 2.5 (7B)",
                provider=ModelProvider.OLLAMA,
                litellm_model_id="ollama/qwen2.5:7b",
                aliases=["qwen2.5"],
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=0.0,  # Free local
                    output_cost_per_million_tokens=0.0,
                ),
                tier_availability=["free"],
                recommended=True,
                priority=100,
            ),
            
            Model(
                id="qwen2.5:14b",
                name="Qwen 2.5 (14B)",
                provider=ModelProvider.OLLAMA,
                litellm_model_id="ollama/qwen2.5:14b",
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=0.0,
                    output_cost_per_million_tokens=0.0,
                ),
                tier_availability=["free"],
                recommended=True,
                priority=95,
            ),
            
            # Llama 3.1 - Meta's latest
            Model(
                id="llama3.1:8b",
                name="Llama 3.1 (8B)",
                provider=ModelProvider.OLLAMA,
                litellm_model_id="ollama/llama3.1:8b",
                aliases=["llama3.1"],
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=0.0,
                    output_cost_per_million_tokens=0.0,
                ),
                tier_availability=["free"],
                recommended=True,
                priority=90,
            ),
            
            # DeepSeek Coder - Best for coding
            Model(
                id="deepseek-coder:6.7b",
                name="DeepSeek Coder (6.7B)",
                provider=ModelProvider.OLLAMA,
                litellm_model_id="ollama/deepseek-coder:6.7b",
                aliases=["deepseek-coder"],
                context_window=16_000,
                capabilities=[
                    ModelCapability.CHAT,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=0.0,
                    output_cost_per_million_tokens=0.0,
                ),
                tier_availability=["free"],
                priority=85,
            ),
            
            # Mistral
            Model(
                id="mistral:7b",
                name="Mistral (7B)",
                provider=ModelProvider.OLLAMA,
                litellm_model_id="ollama/mistral:7b",
                aliases=["mistral"],
                context_window=32_000,
                capabilities=[
                    ModelCapability.CHAT,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=0.0,
                    output_cost_per_million_tokens=0.0,
                ),
                tier_availability=["free"],
                priority=80,
            ),
            
            # Phi-3 - Microsoft's small model
            Model(
                id="phi3:mini",
                name="Phi-3 Mini (3.8B)",
                provider=ModelProvider.OLLAMA,
                litellm_model_id="ollama/phi3:mini",
                aliases=["phi3"],
                context_window=128_000,
                capabilities=[
                    ModelCapability.CHAT,
                ],
                pricing=ModelPricing(
                    input_cost_per_million_tokens=0.0,
                    output_cost_per_million_tokens=0.0,
                ),
                tier_availability=["free"],
                priority=75,
            ),
        ]
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if Ollama is available."""
        import os
        import requests
        
        base_url = os.getenv(cls.api_base_env, cls.default_api_base)
        
        try:
            # Try to connect to Ollama
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @classmethod
    def get_setup_instructions(cls) -> str:
        """Return setup instructions for Ollama."""
        return """
        To use Ollama (local LLM):
        
        1. Download Ollama:
           - Visit https://ollama.ai/download
           - Install for your OS (Windows/Mac/Linux)
        
        2. Pull a model:
           ollama pull qwen2.5:7b
           ollama pull llama3.1
        
        3. Start Ollama (it runs automatically on install)
        
        4. (Optional) Configure base URL in .env:
           OLLAMA_BASE_URL=http://localhost:11434
        
        Features:
        - Completely free
        - No internet required
        - Full privacy (runs locally)
        - Good performance on modern hardware
        - Supports Chinese models (Qwen)
        
        Recommended hardware:
        - 7B models: 8GB+ RAM
        - 14B models: 16GB+ RAM
        - 32B models: 32GB+ RAM (or GPU)
        """
