from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    db_name: str = "inkflow"
    jwt_secret: str
    frontend_url: str = "https://blog.svms.in"
    sso_url: str = "https://accounts.svms.in"
    api_url: str = "https://api.blog.svms.in"

    class Config:
        env_file = ".env"


settings = Settings()
