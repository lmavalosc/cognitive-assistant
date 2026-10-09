from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "nucleo_cognitivo"
    postgres_user: str = "nucleo"
    postgres_password: str = "nucleo"

    redis_host: str = "localhost"
    redis_port: int = 6379

    log_level: str = "INFO"

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # Capa 3: Gobernanza y Autenticación
    guard_risk_threshold: float = 0.70
    api_keys: list[str] = []
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Plano A: LLM Gateway (LiteLLM)
    default_llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_api_key: str | None = None
    llm_api_base: str | None = None
    llm_mock_fallback: bool = True

    # Capa 5: Memoria Persistente (mem0)
    memory_enabled: bool = True
    memory_user_id: str = "default_user"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context) -> None:
        # Si api_keys o cors_allowed_origins vienen como string CSV desde env, convertirlos a lista
        if isinstance(self.api_keys, str):
            self.api_keys = [k.strip() for k in self.api_keys.split(",") if k.strip()]
        if isinstance(self.cors_allowed_origins, str):
            self.cors_allowed_origins = [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

        if self.app_env != "local" and not self.api_keys:
            raise ValueError(
                "Configuración de seguridad inválida: en app_env != 'local' se debe configurar al menos una API key en 'api_keys'."
            )


    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def async_postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


settings = Settings()


def get_settings() -> Settings:
    return settings
