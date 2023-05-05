# Imports

from functools import wraps
from inspect import isawaitable
import httpx
from sanic import Sanic, json, redirect, response
from sanic.log import logger
from sanic_ext import validate
from ib_insync import *
from models.MessageType import MessageType
from bot_handler import send_alert
from models.TradingViewOrder import TradingViewOrder
from order_handler import onFilled
from settings import *
from secret_hash import compareSecret, hashSecret
# Create Sanicobject called app.
app = Sanic(__name__)
app.config.FORWARDED_SECRET = api_secret
app.ctx.ib = IB()


async def checkConnect():
    status = await isConnected()
    if not status:
        await send_alert('API is disconnected. Trying to reconnect it....', MessageType.ERROR)
        try:
            app.ctx.ib = IB()
            await app.ctx.ib.connectAsync(ib_host, ib_port, clientId=1)
            await send_alert('API has been reconnected', MessageType.INFO)
        except Exception as e:
            logger.exception(e)
            await send_alert(getattr(e, 'message', repr(e)), MessageType.ERROR)


async def isConnected():
    connected = True
    if not app.ctx.ib.isConnected() or not app.ctx.ib.client.isConnected():
        connected = False
    return connected


async def positions():
    pos = app.ctx.ib.positions()
    print(util.tree(pos))
    return pos


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


@app.before_server_start
async def firstConnect(app, _):
    status = await isConnected()
    if not status:
        try:
            await app.ctx.ib.connectAsync(ib_host, ib_port, clientId=1)
        except Exception as e:
            logger.exception(e)
            await send_alert(getattr(e, 'message', repr(e)), MessageType.ERROR)


@app.route('/health-check', methods=['GET'])
@authorized(isAdmin=True)
async def connect(request):
    status = await isConnected()
    if not status:
        try:
            await app.ctx.ib.connectAsync(ib_host, ib_port, clientId=1)
            status = await isConnected()
        except Exception as e:
            message = f'''Not able to check health.
            {getattr(e, 'message', repr(e))}
            '''
            logger.exception(e)
            await send_alert(message, MessageType.ERROR)
    return response.json({'Connected': status})


@app.route('/view', methods=['GET'])
@authorized(isAdmin=True)
async def openTws(request):
    status = await isConnected()
    if status:
        return redirect(internal_portal)
    return response.json({'Connected': status})

# Listen for signals and submit orders


@app.route('/webhook', methods=['POST'])
@validate(json=TradingViewOrder)
@authorized
async def webhook(request, body: TradingViewOrder):
    if request.method == 'POST':
        # send alert to channels
        await send_alert(body, MessageType.TRADINGVIEW)

        # Check if we need to reconnect with IB
        await checkConnect()

        future_contract = Future(
            body.ticker[:3].upper(), exchange='CME', includeExpired=False)

        contract_details = await app.ctx.ib.reqContractDetailsAsync(future_contract)

        order = MarketOrder(
            action=body.orderAction.upper(),
            totalQuantity=body.quantity,
            account=app.ctx.ib.wrapper.accounts[0],
            algoStrategy='Adaptive',
            algoParams=[TagValue('adaptivePriority', 'Normal')])
        try:
            ib_order: Trade = app.ctx.ib.placeOrder(
                contract_details[0].contract, order)

            await ib_order.filledEvent
            await send_alert(ib_order, MessageType.CONFIRMATION)
        except Exception as e:
            message = f'''Order not filled?
            {getattr(e, 'message', repr(e))}
            '''
            logger.exception(e)
            await send_alert(message, MessageType.ERROR)

    return json({"result": True})

# For testing purposes
# @app.route('/disconnect')
# async def disconnect(request):
#     app.ctx.ib.disconnect()
#     return json({}, 200)


@app.after_server_stop
def close(app, _):
    app.ctx.ib.disconnect()


# Run App
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000,
            debug=is_debug, access_log=False)
