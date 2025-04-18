from fastapi import FastAPI
from db.database import Base, engine
from routes.routes import router  # <- Make sure you're importing `router` not `app`

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ This is correct:
app.include_router(router)

# ✅ Serve React Frontend Build
if os.path.exists("web"):
    app.mount("/", StaticFiles(directory="web", html=True), name="frontend")

@app.get("/")
async def root():
    return {"message": "LR Entry"}
