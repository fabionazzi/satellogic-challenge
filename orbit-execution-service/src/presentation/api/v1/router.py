from fastapi import APIRouter
from src.presentation.api.v1.routes import constellation, plan

router = APIRouter()
router.include_router(
    constellation.router, prefix="/constellation", tags=["constellation"]
)
router.include_router(plan.router, prefix="/plans", tags=["plans"])
