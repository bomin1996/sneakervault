from fastapi import APIRouter

from app.api.v1 import auth, partners, products, prices, admin, notifications

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(partners.router, prefix="/partners", tags=["Partners"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(prices.router, prefix="/prices", tags=["Prices"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
