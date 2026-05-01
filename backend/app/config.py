"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/thinking_tree"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800

    # Server
    host: str = "127.0.0.1"
    port: int = 8765
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # AI API - Qwen DashScope
    dashscope_api_key: str = ""
    qwen_api_key: str = ""  # Alias for dashscope_api_key
    qwen_model: str = "qwen3.5-omni-flash-realtime"
    qwen_audio_model: str = "qwen3.5-omni-flash-realtime"
    qwen_region: str = "cn"
    qwen_ws_base_url: str = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"

    # AI API - MiMo
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_model: str = "MiMo-V2.5"

    # AI Provider Selection
    ai_provider: str = "qwen"  # "qwen" or "mimo"
    ai_timeout_seconds: int = 30
    ai_max_retries: int = 3
    ai_retry_delay_ms: int = 1000

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60

    # Audio Settings
    audio_sample_rate: int = 16000
    audio_bit_depth: int = 16
    audio_channels: int = 1
    audio_chunk_size: int = 3200

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False

    def get_qwen_api_key(self) -> str:
        """Get Qwen API key (checks both field names)."""
        return self.qwen_api_key or self.dashscope_api_key


settings = Settings()
