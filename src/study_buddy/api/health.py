from fastapi import APIRouter

# our little router, everyone copies this pattern for their endpoint
router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    # just says "I'm alive", the DB check comes later from Storage
    return {"status": "ok"}
