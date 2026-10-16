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