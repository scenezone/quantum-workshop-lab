from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra='ignore')

    app_env: str = 'development'
    log_level: str = 'INFO'

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "quantum_workshop"
    mongodb_timeout_ms: int = 5000

    cors_origins: str = "http://localhost:5173"

    ibm_hardware_enabled: bool = False
    ibm_quantum_api_key: str = ""
    ibm_quantum_instance: str = ""
    ibm_max_daily_jobs: int = 25
    ibm_max_active_jobs: int = 3
    ibm_max_shots: int = 4096


    llm_api_key: str = ''
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_max_requests_per_minute: int = 10
    llm_timeout_seconds: int = 30

    max_simulator_shots: int = 10000
    default_shots: int = 1024

    @property
    def cors_origin_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache()
def get_settings() -> Settings:
    return Settings()