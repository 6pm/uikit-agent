"""
Settings for all ENV variables in the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Infrastructure ---
    ENV: str = "local"
    # Docker Compose will create a service named 'redis'
    # We get this name from the environment variable, or use 'redis' as default.
    REDIS_HOST: str = "redis"

    # --- Huey Settings ---
    TASK_HISTORY_TTL: int = 60 * 60 * 24 * 14  # 14 days default

    # --- Git / Repo Settings ---
    # Path to SSH key (might be empty on local development)
    GIT_SSH_KEY_PATH: str | None = None

    WEB_REPO_PATH: str = "/repos/web"
    MOBILE_REPO_PATH: str = "/repos/mobile"

    WEB_REPO_URL: str
    MOBILE_REPO_URL: str

    # Pydantic will find the .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # needed to trigger the rebuilds in Vercel
    EMAIL_WITH_VERCEL_ACCESS: str = "vercel.email@example.com"


# Create a single instance of settings
settings = Settings()
