from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openrouter_api_key: str
    openrouter_models: str = (
        "deepseek/deepseek-v4-flash:free,"
        "qwen/qwen3-next-80b-a3b-instruct:free,"
        "nvidia/nemotron-3-super-120b-a12b:free,"
        "meta-llama/llama-3.3-70b-instruct:free,"
        "google/gemma-4-31b-it:free,"
        "nousresearch/hermes-3-llama-3.1-405b:free,"
        "openai/gpt-oss-120b:free,"
        "openai/gpt-oss-20b:free,"
        "minimax/minimax-m2.5:free"
    )
    api_key: str
    session_ttl_minutes: int = 30
    kb_folder: str = "K_B"
    allowed_origins: str = "*"

    @property
    def models_list(self) -> list[str]:
        return [m.strip() for m in self.openrouter_models.split(",") if m.strip()]

    @property
    def origins_list(self) -> list[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
