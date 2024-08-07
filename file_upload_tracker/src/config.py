from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    FOLDER_TO_TRACK: str
    FILE_TRACKER: str
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SENDER_EMAIL: str
    RECEIVER_EMAIL: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
