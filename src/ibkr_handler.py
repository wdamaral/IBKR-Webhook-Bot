import asyncio
from ib_insync import IB, Contract, MarketOrder, Position, TagValue, Trade
from sanic.log import logger
from ibkr_events import alert_cancellation, alert_confirmation
from settings import *
from ib_insync import util


async def positions(_ib: IB):
    pos = _ib.positions()

    return pos


async def portfolio(_ib: IB):
    port = _ib.portfolio()

    return port


async def checkConnect(_ib: IB):
    status = await isConnected(_ib)
    if not status:
        try:
            _ib = IB()
            await _ib.connectAsync(ib_host, ib_port, clientId=1)
        except Exception as e:
            logger.exception(e)


async def connect(_ib: IB):
    status = await isConnected(_ib)
    if not status:
        try:
            await _ib.connectAsync(ib_host, ib_port, clientId=1)
            status = await isConnected(_ib)
        except Exception as e:
            message = f'''Not able to check health.
            {getattr(e, 'message', repr(e))}
            '''
            logger.exception(e)

            return message

    return {'Connected': status}


async def close_existing_position(_ib: IB, position: Position):
    order = MarketOrder(
        action='SELL' if position.position > 0 else 'BUY',
        totalQuantity=position.position,
        account=position.account,
        algoStrategy='Adaptive',
        algoParams=[TagValue('adaptivePriority', 'Normal')])
    try:
        ctr = Contract(exchange=__getExchange(position.contract.secType),
                       symbol=position.contract.symbol, secType=position.contract.secType, currency=position.contract.currency)
        contract = await _ib.qualifyContractsAsync(ctr)

        if (len(contract) != 1):
            return 'Ambiguous contract or inexistent.'

        ib_order: Trade = _ib.placeOrder(
            contract[0],
            order)

        ib_order.filledEvent += alert_confirmation
        ib_order.cancelledEvent += alert_cancellation

        return True
    except Exception as e:
        message = f'''Order not filled.
        {getattr(e, 'message', repr(e))}
        '''
        logger.exception(e)
        return message


async def isConnected(_ib: IB):
    connected = True
    if not _ib.isConnected() or not _ib.client.isConnected():
        connected = False
    return connected


def __getExchange(ctrType: str) -> str:
    if (ctrType == 'STK'):
        return 'SMART'

    if (ctrType == 'Future'):
        return 'CME'
