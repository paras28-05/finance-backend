from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Finance Data Processing & Access Control API"
    app_version: str = "1.0.0"
    secret_key: str = "zorvyn-finance-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8  # 8 hours
    database_url: str = "sqlite:///./finance.db"

    class Config:
        env_file = ".env"

settings = Settings()
