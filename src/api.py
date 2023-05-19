# Listen for signals and submit orders
import asyncio
from functools import wraps
from inspect import isawaitable
from ib_insync import (
    MarketOrder,
    TagValue,
    Trade,
    Future
)
from sanic.response import json
from sanic.log import logger
from sanic_ext import validate
from sanic import Blueprint
from bot_handler import (
    send_alert,
    start_bot,
    stop_bot
)
from ibkr_events import alert_cancellation, alert_confirmation
from ibkr_handler import checkConnect, isConnected
from models.MessageType import MessageType
from models.TradingViewOrder import TradingViewOrder
from sanic.log import logger
from sanic_ext import validate
from settings import *

from secret_hash import compareSecret

bp = Blueprint("api")


def authorized(maybe_func=None, *, isAdmin=False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            try:
                reqBody = request.json

                is_authorized = compareSecret(reqBody.get('secret'), isAdmin)

                if is_authorized:
                    response = f(request, *args, **kwargs)
                    if isawaitable(response):
                        response = await response

                    return response
                else:
                    return json({"status": "not_authorized"}, 403)
            except:
                return json({"status": "not_authorized"}, 403)
        return decorated_function
    return decorator(maybe_func) if maybe_func else decorator


@bp.route('/webhook', methods=['POST'])
@validate(json=TradingViewOrder)
@authorized
async def webhook(request, body: TradingViewOrder):
    if request.method == 'POST':
        # send alert to channels
        _ib = bp.apps[0].ctx.ib
        _bot = bp.apps[0].ctx.bot

        await send_alert(_bot, body, MessageType.TRADINGVIEW)

        # Check if we need to reconnect with IB

        await checkConnect(_ib)
        future_contract = Future(
            body.ticker[:3].upper(), exchange='CME', includeExpired=False)

        contract_details = await _ib.reqContractDetailsAsync(future_contract)

        order = MarketOrder(
            action=body.orderAction.upper(),
            totalQuantity=body.quantity,
            account=_ib.wrapper.accounts[0],
            algoStrategy='Adaptive',
            algoParams=[TagValue('adaptivePriority', 'Normal')])
        try:
            ib_order: Trade = _ib.placeOrder(
                contract_details[0].contract, order)

            ib_order.filledEvent += alert_confirmation
            ib_order.cancelledEvent += alert_cancellation

            asyncio.sleep(1)
            # await send_alert(_bot, ib_order, MessageType.CONFIRMATION)
        except Exception as e:
            message = f'''Order not filled?
            {getattr(e, 'message', repr(e))}
            '''
            logger.exception(e)
            await send_alert(_bot, message, MessageType.ERROR)

    return json({"result": True})


@bp.before_server_start
async def ibkr_bot(app, _):
    await start_bot(app)


@bp.before_server_start
async def connect_ibkr(app, _):
    status = await isConnected(app.ctx.ib)
    if not status:
        try:
            await app.ctx.ib.connectAsync(ib_host, ib_port, clientId=1)
        except Exception as e:
            logger.exception(e)
            await send_alert(app.ctx.bot, getattr(e, 'message', repr(e)), MessageType.ERROR)


@bp.before_server_stop
async def server_failure(app, _):
    print('Server closing')
    logger.exception('Server has been shut down')
    await send_alert(app.ctx.bot, 'Server has been shut down', MessageType.ERROR)
# For testing purposes


# @bp.route('/disconnect')
# async def disconnect(request):
#     bp.apps[0].ctx.ib.disconnect()
#     return json({}, 200)


@bp.after_server_stop
async def close(app, _):
    app.ctx.ib.disconnect()
    await stop_bot(app)
