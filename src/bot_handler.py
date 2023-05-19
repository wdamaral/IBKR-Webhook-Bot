from sanic import Sanic
from telegram.ext import Application, CommandHandler
from ib_insync import IB, Trade
from models.MessageType import MessageType
from models.TradingViewOrder import TradingViewOrder
import settings
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler
)
from datetime import tzinfo
from ibkr_handler import close_existing_position, connect, positions
from settings import *
from ib_insync import util


async def send_alert(_bot: Bot, data, message_type: MessageType):
    if (settings.enable_telegram):
        user_bot = _bot.bot
        if message_type == MessageType.TRADINGVIEW:
            message = format_message_tradingview(data)
        elif message_type == MessageType.CONFIRMATION:
            message = format_message_confirmation(data)
        elif message_type == MessageType.ERROR or message_type == MessageType.INFO:
            message = format_message(data, message_type)
        elif message_type == MessageType.CANCELLED:
            message = format_message_cancellation(data)
        else:
            message = data

        await user_bot.send_message(text=message, chat_id=settings.channel_id, parse_mode='HTML')


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
    updown = '📈' if data.order.action.upper() == 'BUY' else '📉'
    message = f'''🔒 🔒 <strong>ALERT - Order filled</strong> 🔒 🔒

Ticker: <i>{data.contract.localSymbol}</i> 🎯 
Quantity: <i>{data.orderStatus.filled}</i> 🧮
Action: <i>{data.order.action}</i> {updown}
Order date: <i>{data.log[len(data.log) - 1].time.astimezone()}</i> 📅
Avg Price: <i>{data.orderStatus.avgFillPrice}</i> 💵
'''

    return message


def format_message_cancellation(data: Trade):
    updown = '📈' if data.order.action.upper() == 'BUY' else '📉'
    message = f'''❌❌ <strong>ALERT - Order cancelled</strong> ❌❌

Ticker: <i>{data.contract.localSymbol}</i> 🎯 
Quantity: <i>{data.order.totalQuantity}</i> 🧮
Action: <i>{data.order.action}</i> {updown}
Reason: <i>{data.log[len(data.log)-1].message}</i>
'''

    return message


def format_message(data, mtype: MessageType):
    if mtype == MessageType.ERROR:
        message = '❌❌❌ ALERT - Error occurred ❌❌❌'
    elif mtype == MessageType.CANCELLED:
        message = '❌❌❌ ALERT - Order cancelled ❌❌❌'
    else:
        message = ' ℹ️ ℹ️ ℹ️ ALERT - Information ℹ️ ℹ️ ℹ️'

    message = f'''{message} 

    {data}
    '''

    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (update.effective_user.id == settings.channel_id):
        await update.message.reply_text(
            '''You are in. Everything works fine. Wait for my updates.'''
        )
    else:
        await update.message.reply_text(
            '''Hey hey! This bot is not active for your user and you will not receive anything.'''
        )


async def reconnect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (update.effective_user.id == settings.channel_id):
        app = Sanic.get_app()
        isConnected = await connect(app.ctx.ib)

        await update.message.reply_text(
            isConnected
        )


async def get_positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (update.effective_user.id == settings.channel_id):
        app = Sanic.get_app()

        pos = await positions(app.ctx.ib)

        if len(pos) > 0:
            message = 'See below your current positions.'
            for i in pos:
                message = message + f'''
                _____________________
                Account: {i.account},
                Symbol: {i.contract.localSymbol}
                Position: {i.position}
                AvgCost: {i.avgCost}
                _____________________
                '''
        else:
            message = 'You do not have any positions open.'

        await update.message.reply_text(
            message
        )


async def panic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (update.effective_user.id == settings.channel_id):

        keyboard = [
            [InlineKeyboardButton('Yes, cancel!', callback_data='YES')],
            [InlineKeyboardButton('No!', callback_data='NO')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            '''Hey! This is the panic mode. If you say YES, I will close all your positions.
            Are you sure you want to do that??''',
            reply_markup=reply_markup
        )


async def close_positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if (update.effective_user.id == settings.channel_id):
        query = update.callback_query

        await query.answer()

        if query.data == 'YES':
            app = Sanic.get_app()
            await query.edit_message_text(text=f'Ok! Running the requests...')
            pos = await positions(app.ctx.ib)

            if len(pos) > 0:
                for p in pos:
                    result = close_existing_position(app.ctx.ib, p)

                    if result == True:
                        message = f'Request to close position in {p.contract.localSymbol} sent.'
                    else:
                        message = f'Something happened and request to close position in {p.contract.localSymbol} failed.\n\n{result}'

                    await query.message.reply_text(message)
            else:
                await query.message.reply_text('You do not have any open positions.')
        else:
            await query.edit_message_text(text=f'No problem! Rest assured nothing will be done.')


async def start_bot(app: Sanic):
    if settings.enable_telegram:
        app.ctx.bot = Application.builder().token(telegram_token).build()
        app.ctx.bot.add_handler(CommandHandler("start", start))
        app.ctx.bot.add_handler(CommandHandler("healthcheck", reconnect))
        app.ctx.bot.add_handler(CommandHandler('panic', panic))
        app.ctx.bot.add_handler(CallbackQueryHandler(close_positions,))
        app.ctx.bot.add_handler(CommandHandler('openpositions', get_positions))
        await app.ctx.bot.initialize()
        await app.ctx.bot.updater.start_polling()
        await app.ctx.bot.start()


async def stop_bot(app: Sanic):
    if settings.enable_telegram:
        await app.ctx.bot.updater.stop()
        await app.ctxbo.t.stop()
        await app.ctx.bot.shutdown()
