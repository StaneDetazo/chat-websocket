from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.endpoints import users, rooms
from app.config import settings
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Action au démarrage de l'application : Initialisation de la base de données
    init_db()
    yield
    # Action à l'arrêt de l'application
    pass

app = FastAPI(
    title=settings.APP_NAME,
    description="API REST et WebSocket pour l'application de Chat en temps réel",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

@app.get("/", tags=["Welcome"])
def welcome():
    return {"message": "Bienvenue sur l'API de Chat en temps réel!"}

@app.get("/health", tags=["Healthcheck"])
def health_check():
    """
    Endpoint de vérification de l'état de l'application.
    Permet de vérifier que l'API tourne correctement.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "debug_mode": settings.DEBUG
    }

app.include_router(users.router)
app.include_router(rooms.router)
