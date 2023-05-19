# Executors of IBKR events

from ib_insync import Trade
from sanic import Sanic
import bot_handler
from models.MessageType import MessageType


async def alert_confirmation(trade: Trade):
    app = Sanic.get_app()
    _bot = app.ctx.bot

    await bot_handler.send_alert(_bot, trade, MessageType.CONFIRMATION)


async def alert_cancellation(trade: Trade):
    app = Sanic.get_app()
    _bot = app.ctx.bot

    await bot_handler.send_alert(_bot, trade, MessageType.CANCELLED)
