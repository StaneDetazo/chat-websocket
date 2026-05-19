from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Arguments additionnels pour la connexion (utiles pour SQLite)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Création du moteur de base de données SQLAlchemy (synchrone)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True  # Vérifie la validité des connexions du pool
)

# Générateur de sessions de base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """
    Initialise la base de données en créant toutes les tables définies dans les modèles.
    Crée également la base de données MySQL si elle n'existe pas encore.
    """
    # Si nous utilisons MySQL, on tente de créer la base de données si elle n'existe pas
    url = make_url(settings.DATABASE_URL)
    if url.drivername.startswith("mysql"):
        # On se connecte sans spécifier de base de données
        temp_url = url._replace(database=None)
        temp_engine = create_engine(temp_url)
        with temp_engine.connect() as conn:
            # On exécute la requête de création de base
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{url.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
        temp_engine.dispose()

    from app.models.base import Base
    # Import des modèles pour enregistrement sur Base.metadata
    import app.models.user
    import app.models.room
    import app.models.message
    
    Base.metadata.create_all(bind=engine)
