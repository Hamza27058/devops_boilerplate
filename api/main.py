from fastapi import FastAPI
from api.routers.user import router as user_router
from api.routers.role import router as role_router
from api.dependencies import engine
from api.models import Base

app = FastAPI()

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

app.include_router(user_router)
app.include_router(role_router)
