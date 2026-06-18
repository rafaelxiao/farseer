from fastapi import APIRouter

from farseer.api.v1.ohlc import router as ohlc_router
from farseer.api.v1.fundamentals import router as fundamentals_router
from farseer.api.v1.tasks import router as tasks_router
from farseer.api.v1.fetch import router as fetch_router
from farseer.api.v1.auth import router as auth_router
from farseer.api.v1.trading_game import router as trading_game_router

router = APIRouter()

router.include_router(ohlc_router, prefix="/ohlc", tags=["OHLC"])
router.include_router(fundamentals_router, prefix="/fundamentals", tags=["Fundamentals"])
router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
router.include_router(fetch_router, prefix="/fetch", tags=["Fetch"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(trading_game_router, prefix="/game", tags=["Trading Game"])
