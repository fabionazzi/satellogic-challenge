from fastapi import APIRouter
from src.presentation.api.v1.routes import capture

router = APIRouter()
router.include_router(capture.router, prefix="/captures", tags=["captures"])
