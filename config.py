"""
API配置文件 - 集中管理所有API密钥和应用配置

使用方法：
1. 复制 .env.example 为 .env
2. 在 .env 中填入你的API密钥
3. 运行 python config.py 检查配置

支持的API提供商：
- 硅基流动 (SiliconFlow) - 主要风格分析API
- OpenAI - 可选备用API
- Hugging Face - 模型下载和Token认证
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class APIConfig:
    """API配置管理类"""

    def __init__(self):
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # ========================================
        # 硅基流动API配置 (主要)
        # ========================================
        self.SILICONFLOW_API_KEY: Optional[str] = os.getenv("SILICONFLOW_API_KEY")
        self.SILICONFLOW_BASE_URL: str = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        self.SILICONFLOW_MODEL: str = os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V2.5")
        self.SILICONFLOW_TIMEOUT: int = int(os.getenv("SILICONFLOW_TIMEOUT", "30"))

        # ========================================
        # OpenAI API配置 (可选备用)
        # ========================================
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.OPENAI_TIMEOUT: int = int(os.getenv("OPENAI_TIMEOUT", "30"))

        # ========================================
        # 通义千问API配置 (可选)
        # ========================================
        self.QWEN_API_KEY: Optional[str] = os.getenv("QWEN_API_KEY")
        self.QWEN_BASE_URL: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        self.QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-turbo")

        # ========================================
        # 智谱AI配置 (可选)
        # ========================================
        self.ZHIPU_API_KEY: Optional[str] = os.getenv("ZHIPU_API_KEY")
        self.ZHIPU_BASE_URL: str = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        self.ZHIPU_MODEL: str = os.getenv("ZHIPU_MODEL", "glm-4")

        # ========================================
        # Hugging Face配置
        # ========================================
        self.HF_ENDPOINT: str = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
        self.HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
        self.HF_CACHE_DIR: str = os.getenv("HF_CACHE_DIR", "~/.cache/huggingface")

    def get_available_apis(self) -> Dict[str, bool]:
        """获取可用的API列表"""
        return {
            "siliconflow": bool(self.SILICONFLOW_API_KEY),
            "openai": bool(self.OPENAI_API_KEY),
            "qwen": bool(self.QWEN_API_KEY),
            "zhipu": bool(self.ZHIPU_API_KEY),
        }

    def get_primary_api(self) -> str:
        """获取主要使用的API"""
        available = self.get_available_apis()
        if available["siliconflow"]:
            return "siliconflow"
        elif available["openai"]:
            return "openai"
        elif available["qwen"]:
            return "qwen"
        elif available["zhipu"]:
            return "zhipu"
        else:
            return "none"


class ModelConfig:
    """模型配置管理类"""

    def __init__(self):
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 默认模型
        self.DEFAULT_MODEL: str = os.getenv("MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")

        # 支持的模型列表
        self.SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
            "Qwen/Qwen2.5-0.5B-Instruct": {
                "name": "Qwen 2.5 0.5B",
                "description": "通义千问2.5，轻量级中文模型",
                "size": "0.5B",
                "language": "中文优先"
            },
            "Qwen/Qwen2.5-1.5B-Instruct": {
                "name": "Qwen 2.5 1.5B",
                "description": "通义千问2.5，中等尺寸中文模型",
                "size": "1.5B",
                "language": "中文优先"
            },
            "distilgpt2": {
                "name": "DistilGPT-2",
                "description": "轻量级GPT-2，快速响应",
                "size": "82M",
                "language": "英文"
            },
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0": {
                "name": "TinyLlama 1.1B",
                "description": "小型Llama模型，性能均衡",
                "size": "1.1B",
                "language": "英文"
            }
        }

        # 模型下载配置
        self.MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "~/.cache/huggingface")
        self.MODEL_DOWNLOAD_TIMEOUT: int = int(os.getenv("MODEL_DOWNLOAD_TIMEOUT", "300"))

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        return self.SUPPORTED_MODELS.get(model_id)


class StyleConfig:
    """风格配置管理类"""

    def __init__(self):
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 默认风格模板
        self.default_style_templates: Dict[str, str] = {
            "Senku科学家风格": "You are Senku from the manga Dr. Stone. You speak with a scientific mindset: conclusions first, then clear step-by-step explanations. When uncertain, propose hypotheses and experiments to test them. Occasionally exclaim '10 billion percent' when emphasising facts. Always keep answers structured and logical, like a scientist.",
            "专业技术专家": "你是一位资深的技术专家，擅长解释复杂的技术概念。你会用准确的技术术语，逻辑清晰地回答问题，同时会考虑用户的知识水平进行适当的解释。",
            "友好生活助手": "你是一个友好的生活助手，像一个贴心的朋友一样与用户交流。你会用温暖、亲切的语气，提供实用的生活建议和解决方案。",
            "幽默段子手": "你是一个幽默风趣的段子手，擅长用轻松愉快的语气与用户聊天。你会用一些俏皮话和双关语，让对话变得更有趣。",
            "严谨学者": "你是一位严谨的学者，注重逻辑和证据。你会用正式的学术语言，引用事实和数据来支持你的观点。",
            "创意艺术家": "你是一位富有创意的艺术家，用诗意的语言和丰富的想象力与用户交流。你会用比喻、象征等艺术手法来表达想法。",
            "耐心导师": "你是一位耐心细致的导师，像教导学生一样与用户交流。你会循序渐进地解释概念，经常检查用户是否理解。",
            "俏皮机智": "你机智幽默，反应敏捷。你会用俏皮的语言和机智的回应，让对话充满乐趣和智慧。",
            "温柔治愈": "你温柔体贴，像一个治愈系的朋友。你用温暖的话语和积极的态度，帮助用户缓解压力和焦虑。",
        }

        # 风格分析配置
        self.STYLE_ANALYSIS_TIMEOUT: int = int(os.getenv("STYLE_ANALYSIS_TIMEOUT", "30"))


class ServerConfig:
    """服务器配置管理类"""

    def __init__(self):
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 服务器基本配置
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.WORKERS: int = int(os.getenv("WORKERS", "1"))

        # CORS配置
        self.CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
        self.CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

        # 安全配置
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
        self.API_KEY_REQUIRED: bool = os.getenv("API_KEY_REQUIRED", "false").lower() == "true"

        # 日志配置
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE: Optional[str] = os.getenv("LOG_FILE")


class TaskConfig:
    """任务处理配置管理类"""

    def __init__(self):
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # Redis配置
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

        # Celery配置
        self.CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", self.REDIS_URL)
        self.CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", self.REDIS_URL)
        self.CELERY_TASK_TIMEOUT: int = int(os.getenv("CELERY_TASK_TIMEOUT", "3600"))

        # 任务队列配置
        self.MAX_CONCURRENT_TASKS: int = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
        self.TASK_CLEANUP_INTERVAL: int = int(os.getenv("TASK_CLEANUP_INTERVAL", "3600"))


class Config:
    """主配置类 - 统一管理所有配置"""

    def __init__(self):
        self.api = APIConfig()
        self.model = ModelConfig()
        self.style = StyleConfig()
        self.server = ServerConfig()
        self.task = TaskConfig()

        # 向后兼容的属性
        self.SILICONFLOW_API_KEY = self.api.SILICONFLOW_API_KEY
        self.SILICONFLOW_BASE_URL = self.api.SILICONFLOW_BASE_URL
        self.SILICONFLOW_MODEL = self.api.SILICONFLOW_MODEL
        self.OPENAI_API_KEY = self.api.OPENAI_API_KEY
        self.HF_ENDPOINT = self.api.HF_ENDPOINT
        self.HF_TOKEN = self.api.HF_TOKEN
        self.DEFAULT_MODEL = self.model.DEFAULT_MODEL
        self.REDIS_URL = self.task.REDIS_URL
        self.HOST = self.server.HOST
        self.PORT = self.server.PORT
        self.DEBUG = self.server.DEBUG

        # 功能配置
        self.STYLE_ANALYSIS_TIMEOUT: int = 30
        self.STYLE_ANALYSIS_MAX_TOKENS: int = 1000
        self.FINETUNE_DEFAULT_EPOCHS: int = 3
        self.FINETUNE_DEFAULT_LR: float = 2e-5
        self.FINETUNE_DEFAULT_BATCH_SIZE: int = 4
        self.FINETUNE_MAX_EPOCHS: int = 10
        self.FINETUNE_MAX_BATCH_SIZE: int = 16
        self.CHAT_DEFAULT_MAX_TOKENS: int = 256
        self.CHAT_DEFAULT_TEMPERATURE: float = 0.7
        self.CHAT_DEFAULT_TOP_P: float = 0.9

        # 存储配置
        self.STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # local, s3, google_drive
        self.MODELS_DIR: str = os.getenv("MODELS_DIR", "models")

        # AWS S3配置
        self.AWS_S3_BUCKET: Optional[str] = os.getenv("AWS_S3_BUCKET")
        self.AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
        self.AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")

        # Google Drive配置
        self.GOOGLE_DRIVE_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_DRIVE_CREDENTIALS")

        # 服务端点配置
        self.SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")
        self.CLIENT_URL: str = os.getenv("CLIENT_URL", "http://localhost:5000")

        # SSH配置
        self.SSH_HOSTNAME: Optional[str] = os.getenv("SSH_HOSTNAME")
        self.SSH_USERNAME: str = os.getenv("SSH_USERNAME", "root")
        self.SSH_KEY_FILENAME: Optional[str] = os.getenv("SSH_KEY_FILENAME")
        self.SSH_REMOTE_WORKSPACE: str = os.getenv("SSH_REMOTE_WORKSPACE", "/root/workspace")

    @classmethod
    def validate_config(cls) -> list[str]:
        """验证配置并返回警告信息"""
        config = cls()
        warnings = []

        # 检查API配置
        available_apis = config.api.get_available_apis()
        if not available_apis["siliconflow"]:
            warnings.append("⚠️  硅基流动API密钥未配置，将使用本地风格分析")

        if not any(available_apis.values()):
            warnings.append("❌ 没有配置任何AI API，可能影响部分功能")

        # 检查模型配置
        if config.model.DEFAULT_MODEL not in config.model.SUPPORTED_MODELS:
            warnings.append(f"⚠️  默认模型 '{config.model.DEFAULT_MODEL}' 不在支持列表中")

        # 检查服务器配置
        if config.server.DEBUG:
            warnings.append("ℹ️  调试模式已启用，请在生产环境中关闭")

        return warnings

    @classmethod
    def load_from_env_file(cls, env_file: str = ".env") -> 'Config':
        """
        从环境变量文件加载配置。

        尝试使用 python‑dotenv 加载 `.env` 文件中的配置。如果没有安装
        `python‑dotenv` 或导入失败，则静默跳过，不影响程序的其他部分。
        """
        if Path(env_file).exists():
            try:
                # Importing within the try block prevents ImportError when the
                # python‑dotenv package is not installed. Failing gracefully here
                # allows this module to be imported in lightweight environments.
                from dotenv import load_dotenv  # type: ignore
                load_dotenv(env_file)
            except Exception:
                # Could log a warning here if desired, but silently ignore to
                # maintain compatibility with minimal installations.
                pass

        return cls()

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "apis": self.api.get_available_apis(),
            "primary_api": self.api.get_primary_api(),
            "default_model": self.model.DEFAULT_MODEL,
            "server": f"{self.server.HOST}:{self.server.PORT}",
            "debug": self.server.DEBUG,
            "redis": self.task.REDIS_URL,
            "hf_endpoint": self.api.HF_ENDPOINT
        }

    def is_api_configured(self) -> bool:
        """检查是否有API配置"""
        available_apis = self.api.get_available_apis()
        return any(available_apis.values())

    def get_style_templates(self) -> Dict[str, str]:
        """获取风格模板"""
        return self.style.default_style_templates

    def get_supported_models(self) -> Dict[str, Dict[str, Any]]:
        """获取支持的模型列表"""
        return self.model.SUPPORTED_MODELS


# 全局配置实例
config = Config.load_from_env_file()


def reload_config() -> None:
    """重新加载配置（用于运行时配置更新）"""
    global config
    config = Config.load_from_env_file()


# 配置检查和显示
if __name__ == "__main__":
    print("🔧 API配置检查结果:")
    warnings = Config.validate_config()
    if warnings:
        for warning in warnings:
            print(f"   {warning}")
    else:
        print("   ✅ 所有必需配置已正确设置")

    print("\n📋 当前配置摘要:")
    summary = config.get_config_summary()
    print(f"   🤖 主要API: {summary['primary_api']}")
    print(f"   📊 可用API: {', '.join([k for k, v in summary['apis'].items() if v])}")
    print(f"   🧠 默认模型: {summary['default_model']}")
    print(f"   🚀 服务器: {summary['server']}")
    print(f"   🔗 Redis: {summary['redis']}")
    print(f"   🌐 HF镜像: {summary['hf_endpoint']}")
    if summary['debug']:
        print("   🐛 调试模式: 已启用")

# 全局配置实例
config = Config.load_from_env_file()


def reload_config() -> None:
    """重新加载配置（用于运行时配置更新）"""
    global config
    config = Config.load_from_env_file()


# 配置检查和显示
if __name__ == "__main__":
    print("🔧 API配置检查结果:")
    warnings = Config.validate_config()
    if warnings:
        for warning in warnings:
            print(f"   {warning}")
    else:
        print("   ✅ 所有必需配置已正确设置")

    print("\n📋 当前配置摘要:")
    summary = config.get_config_summary()
    print(f"   🤖 主要API: {summary['primary_api']}")
    print(f"   📊 可用API: {', '.join([k for k, v in summary['apis'].items() if v])}")
    print(f"   🧠 默认模型: {summary['default_model']}")
    print(f"   🚀 服务器: {summary['server']}")
    print(f"   🔗 Redis: {summary['redis']}")
    print(f"   🌐 HF镜像: {summary['hf_endpoint']}")
    if summary['debug']:
        print("   🐛 调试模式: 已启用")
