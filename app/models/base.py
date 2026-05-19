from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Classe de base déclarative pour tous les modèles SQLAlchemy de l'application.
    Tous les modèles de base de données hériteront de cette classe.
    """
    pass
