from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_port: int = 8082

    evolution_api_url: str = "http://localhost:8080"
    evolution_api_key: str = ""
    evolution_instance: str = "emporio"

    pix_chave: str = "66398590000160"
    pix_nome: str = "Empório Canastra DF"
    pix_cidade: str = "BRASILIA"
    pix_qrcode_path: str = "static/img/qrcode.png"

    database_url: str = "sqlite:///./data/emporiodb.sqlite"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
