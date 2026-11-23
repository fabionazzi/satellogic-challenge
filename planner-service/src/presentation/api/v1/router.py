from fastapi import APIRouter

from src.presentation.api.v1.routes import capture, simulations

router = APIRouter()
router.include_router(capture.router, prefix="/captures", tags=["captures"])
router.include_router(
    simulations.router, prefix="/simulations", tags=["simulations"]
)
