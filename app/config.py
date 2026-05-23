from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Configuration générale de l'application
    APP_NAME: str = "WoChat"
    DEBUG: bool = True

    # Configuration de la base de données
    DATABASE_URL: str

    # Configuration de la sécurité JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Charge les variables depuis le fichier .env
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

# Instance globale des paramètres à importer dans l'application
settings = Settings()
