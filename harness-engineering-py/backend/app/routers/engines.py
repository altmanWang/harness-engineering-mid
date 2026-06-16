from fastapi import APIRouter
from app.services.engine_factory import detect_engines

router = APIRouter()


@router.get("/engines/availability")
async def get_engine_availability():
    engines = await detect_engines()
    return {"engines": [e.model_dump() for e in engines]}
