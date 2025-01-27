import logging
from aiogram import BaseMiddleware
from aiogram.types import Message

log = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        log.info(f"Получено сообщение: {event.text}")
        print(f"Получено сообщение: {event.text}")
        return await handler(event, data)
