from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    folder_to_track: str
    file_tracker: str
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    sender_email: str
    receiver_email: str
    client_id: str
    client_secret_id: str
    auth_url: str
    one_drive_file_tracker: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
