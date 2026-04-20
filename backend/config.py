from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TN Scheme Compass API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    mysql_url: str | None = None
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str | None = None
    mysql_database: str = "tn_scheme_compass"
    scheme_csv_path: str = "data_collection/outputs/welfare_schemes_tamil_nadu.csv"

    chroma_path: str = "chroma_store"
    chroma_collection_name: str = "tn_welfare_schemes"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    retrieval_top_k: int = 5

    @property
    def database_url(self) -> str:
        if self.mysql_url and self.mysql_url.strip():
            return self.mysql_url.strip()

        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password) if self.mysql_password else ""
        host = self.mysql_host
        port = self.mysql_port
        dbname = self.mysql_database

        if password:
            auth = f"{user}:{password}"
        else:
            auth = user

        return f"mysql+pymysql://{auth}@{host}:{port}/{dbname}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
