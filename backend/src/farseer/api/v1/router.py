from fastapi import APIRouter

from farseer.api.v1.ohlc import router as ohlc_router
from farseer.api.v1.fundamentals import router as fundamentals_router
from farseer.api.v1.tasks import router as tasks_router

router = APIRouter()

router.include_router(ohlc_router, prefix="/ohlc", tags=["OHLC"])
router.include_router(fundamentals_router, prefix="/fundamentals", tags=["Fundamentals"])
router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
