from fastapi import FastAPI

from study_buddy.api import health

# the one and only app, it just plugs in the routers
app = FastAPI(title="Study Buddy")

app.include_router(health.router)
# each track adds their own line here when their endpoint is ready:
# app.include_router(upload.router)      Ingestion
# app.include_router(ask.router)         Retrieval & Generation
# app.include_router(documents.router)   Storage
