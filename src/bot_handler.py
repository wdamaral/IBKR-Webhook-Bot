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
        elif message_type == MessageType.ERROR or MessageType.INFO:
            message = format_message(data, message_type)
        else:
            message = data

        async with bot:
            await bot.send_message(text=message, chat_id=settings.channel_id, parse_mode='HTML')


def format_message_tradingview(data: TradingViewOrder):
    updown = '📈' if data.orderAction == 'BUY' else '📉'
    message = f'''📣 📣 <strong>ALERT - Order received</strong> 📣 📣
    
Ticker: <i>{data.ticker}</i> 🎯
Quantity: <i>{data.quantity}</i> 🧮
Action: <i>{data.orderAction}</i>  {updown}
Price: <i>{data.price}</i> 💵
Order date: <i>{data.orderDate.astimezone()}</i> 📅
Current position: <i>{data.currentPositionSize}</i>
Current position type: <i>{data.currentPositionType}</i>
'''

    return message


def format_message_confirmation(data: Trade):
    updown = '📈' if data.orderAction == 'BUY' else '📉'
    message = f'''🔒 🔒 <strong>ALERT - Order filled</strong> 🔒 🔒

Ticker: <i>{data.contract.localSymbol}</i> 🎯 
Quantity: <i>{data.orderStatus.filled}</i> 🧮
Action: <i>{data.order.action}</i> {updown}
Order date: <i>{data.log[len(data.log) - 1].time.astimezone()}</i> 📅
Avg Price: <i>{data.orderStatus.avgFillPrice}</i> 💵
'''

    return message


def format_message(data, mtype: MessageType):
    message = '❌❌❌ ALERT - Error occurred ❌❌❌' if mtype == MessageType.ERROR else ' ℹ️ ℹ️ ℹ️ ALERT - Information ℹ️ ℹ️ ℹ️'
    message = f'''{message} 

    {data}
    '''

    return message
