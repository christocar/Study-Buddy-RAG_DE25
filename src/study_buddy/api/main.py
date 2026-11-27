from fastapi import FastAPI

from study_buddy.api import ask, health, upload, youtube

# the one and only app, it just plugs in the routers
app = FastAPI(title="Study Buddy")

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(ask.router)
app.include_router(youtube.router)
# each track adds their own line here when their endpoint is ready:
# app.include_router(documents.router)   Storage
