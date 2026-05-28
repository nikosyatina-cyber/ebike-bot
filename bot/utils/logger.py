import sys
from loguru import logger
from core.settings import settings

def setup_logger():
    logger.remove()
    log_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>"
    logger.add(sys.stdout, format=log_format, level=settings.log_level, colorize=True)
    logger.add("logs/ebike_{time:YYYY-MM-DD}.log", format=log_format, level="DEBUG", rotation="00:00", retention="7 days", compression="zip", encoding="utf-8")
    return logger

log = setup_logger()