from ib_insync import Trade
from models.MessageType import MessageType
from models.TradingViewOrder import TradingViewOrder
import settings
from telegram import Bot
from datetime import tzinfo


async def send_alert(data, message_type: MessageType):

    if (settings.enable_telegram):
        bot = Bot(settings.telegram_token)

        if message_type == MessageType.TRADINGVIEW:
            message = format_message_tradingview(data)
        elif message_type == MessageType.CONFIRMATION:
            message = format_message_confirmation(data)
        elif message_type == MessageType.ERROR:
            message = format_message_error(data)
        else:
            message = data

        async with bot:
            await bot.send_message(text=message, chat_id=settings.channel_id)


def format_message_tradingview(data: TradingViewOrder):
    message = f'''--- ALERT - Order received ----
    
    Ticker: {data.ticker}
    Quantity: {data.quantity}
    Action: {data.orderAction}
    Price: {data.price}
    Order date: {data.orderDate.astimezone()}
    Current position: {data.currentPositionSize}
    Current position type: {data.currentPositionType}
    '''

    return message


def format_message_confirmation(data: Trade):
    message = f'''+++ ALERT - Order filled +++

    Ticker: {data.contract.localSymbol}
    Quantity: {data.orderStatus.filled}
    Action: {data.order.action}
    Order date: {data.log[len(data.log) - 1].time.astimezone()}
    Avg Price: {data.orderStatus.avgFillPrice}
    '''

    return message


def format_message_error(data):
    message = f''' !-!-!- ALERT - Error occurred -!-!-! 

    {data}
    '''

    return message
