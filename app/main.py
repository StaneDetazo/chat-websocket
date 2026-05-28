import time
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from app.api.endpoints import users, rooms, auth, messages, admin
from app.config import settings
from app.database import init_db
from app.websocket.handler import handle_websocket_main

RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60
request_counts: dict[str, list[float]] = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="API REST et WebSocket pour l'application de Chat en temps réel",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
    swagger_ui_parameters={"persistAuthorization": True}
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    times = request_counts[client_ip]
    times = [t for t in times if now - t < RATE_LIMIT_WINDOW]
    request_counts[client_ip] = times
    if len(times) >= RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Trop de requêtes. Veuillez ralentir."}
        )
    times.append(now)
    response = await call_next(request)
    return response


@app.get("/", tags=["Welcome"])
def welcome():
    return {"message": "Bienvenue sur l'API de Chat en temps réel!"}


@app.get("/health", tags=["Healthcheck"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "debug_mode": settings.DEBUG
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket_main(websocket)


@app.websocket("/ws/rooms/{room_id}")
async def websocket_room_endpoint(websocket: WebSocket, room_id: int):
    await handle_websocket_main(websocket)


API_PREFIX = "/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(rooms.router, prefix=API_PREFIX)
app.include_router(messages.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
