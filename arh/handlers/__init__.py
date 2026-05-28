from .xp import router
from .karma import router as karma_router
from .profile import router as profile_router
from .market import router as market_router
from .alerts import router as alerts_router

# Объединяем все роутеры в список
routers = [router, karma_router, profile_router, market_router, alerts_router]