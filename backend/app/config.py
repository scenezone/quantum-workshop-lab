from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import Field, model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = 'development'
    log_level: str = 'INFO'

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "quantum_workshop"
    mongodb_timeout_ms: int = Field(default=5000, ge=100)
    mongodb_connect_attempts: int = Field(default=5, ge=1, le=20)

    cors_origins: str = "http://localhost:5173"

    ibm_hardware_enabled: bool = False
    ibm_quantum_api_key: str = ""
    ibm_quantum_instance: str = ""
    ibm_max_daily_jobs: int = Field(default=25, ge=0)
    ibm_max_active_jobs: int = Field(default=3, ge=0)
    ibm_max_shots: int = Field(default=4096, ge=1)
    job_poll_seconds: int = Field(default=15, ge=1)
    job_retention_days: int = Field(default=7, ge=1)


    llm_api_key: str = ''
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-20b"
    llm_max_requests_per_minute: int = Field(default=10, ge=1)
    llm_timeout_seconds: int = Field(default=25, ge=1)
    rate_limit_storage_uri: str = 'memory://'

    max_simulator_shots: int = Field(default=10000, ge=1)
    default_shots: int = Field(default=1024, ge=1)

    @model_validator(mode='after')
    def validate_shots(self):
        if self.default_shots > self.max_simulator_shots:
            raise ValueError('DEFAULT_SHOTS must not exceed MAX_SIMULATOR_SHOTS')
        return self

    @property
    def cors_origin_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache()
def get_settings() -> Settings:
    return Settings()
