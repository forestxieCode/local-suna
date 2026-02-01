"""配置加载和管理"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # 加载环境变量
        load_dotenv()
        
        # 加载配置文件
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = self._load_config()
        
        # 替换环境变量
        self._substitute_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _substitute_env_vars(self):
        """替换配置中的环境变量 ${VAR_NAME}"""
        self._substitute_dict(self.config)
    
    def _substitute_dict(self, d: Dict[str, Any]):
        """递归替换字典中的环境变量"""
        for key, value in d.items():
            if isinstance(value, dict):
                self._substitute_dict(value)
            elif isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                d[key] = os.getenv(env_var, '')
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        获取配置值
        例如: config.get('llm.model') -> 'qwen-turbo'
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def llm_provider(self) -> str:
        return self.get('llm.provider', 'dashscope')
    
    @property
    def llm_api_key(self) -> str:
        # 优先从环境变量获取
        return os.getenv('DASHSCOPE_API_KEY') or self.get('llm.api_key', '')
    
    @property
    def llm_model(self) -> str:
        return self.get('llm.model', 'qwen-turbo')
    
    @property
    def llm_temperature(self) -> float:
        return float(self.get('llm.temperature', 0.7))
    
    @property
    def llm_max_tokens(self) -> int:
        return int(self.get('llm.max_tokens', 2000))
    
    @property
    def sandbox_enabled(self) -> bool:
        return bool(self.get('sandbox.enabled', True))
    
    @property
    def sandbox_image(self) -> str:
        return self.get('sandbox.image', 'python:3.11-slim')
    
    @property
    def sandbox_timeout(self) -> int:
        return int(self.get('sandbox.timeout', 60))
    
    @property
    def sandbox_memory_limit(self) -> int:
        return int(self.get('sandbox.memory_limit', 512))
    
    @property
    def history_save_to_file(self) -> bool:
        return bool(self.get('history.save_to_file', True))
    
    @property
    def history_file_path(self) -> str:
        return self.get('history.file_path', './conversations/')
    
    @property
    def history_max_messages(self) -> int:
        return int(self.get('history.max_messages', 50))
    
    @property
    def log_level(self) -> str:
        return self.get('logging.level', 'INFO')


# 全局配置实例
config: Optional[Config] = None

def init_config(config_path: str = "config.yaml") -> Config:
    """初始化全局配置"""
    global config
    config = Config(config_path)
    return config

def get_config() -> Config:
    """获取全局配置实例"""
    global config
    if config is None:
        config = init_config()
    return config
