from fastapi import APIRouter

from .routes.health import router as health_router
from .routes.admin import router as admin_router
from .routes.books import router as books_router
from .routes.stats import router as stats_router

router = APIRouter(prefix="/v1")

router.include_router(health_router)
router.include_router(admin_router)
router.include_router(books_router)
router.include_router(stats_router)
