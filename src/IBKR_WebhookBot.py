# Imports

from datetime import datetime
from sanic import Sanic
from sanic import response
from ib_insync import *

# Create Sanicobject called app.
app = Sanic(__name__)
app.ctx.ib = None


@app.before_server_start
async def connect(app, _):
    app.ctx.ib = IB()
    await app.ctx.ib.connectAsync('127.0.0.1', 8888, clientId=1)

# Create root to easily let us know its on/working.


@app.route('/')
async def root(request):
    return response.text('online')

# Listen for signals and submit orders


@app.route('/webhook-buy', methods=['POST'])
async def webhookBuy(request):
    if request.method == 'POST':
        # Check if we need to reconnect with IB
        await checkIfReconnect()
        # Parse the string data from tradingview into a python dict
        data = request.json
        order = MarketOrder("BUY", 1, account=app.ib.wrapper.accounts[0])
        # contract = Crypto(data['symbol'][0:3],'PAXOS',data['symbol'][3:6]) #Get first 3 chars BTC then last 3 for currency USD
        # or stock for example
        contract = Stock('AAPL', 'SMART', 'USD')
        app.ib.placeOrder(contract, order)
    return response.json({})


@app.route('/webhook-sell', methods=['POST'])
async def webhookSell(request):
    if request.method == 'POST':
        # Check if we need to reconnect with IB
        await checkIfReconnect()
        # Parse the string data from tradingview into a python dict
        data = request.json
        order = MarketOrder("SELL", 1, account=app.ctx.ib.wrapper.accounts[0])
        # contract = Crypto(data['symbol'][0:3],'PAXOS',data['symbol'][3:6]) #Get first 3 chars BTC then last 3 for currency USD
        # or stock for example
        contract = Stock('AAPL', 'SMART', 'USD')
        app.ctx.ib.placeOrder(contract, order)
    return response.json({})

# Check every minute if we need to reconnect to IB


async def checkIfReconnect():
    if not app.ctx.ib.isConnected() or not app.ctx.ib.client.isConnected():
        app.ctx.ib.disconnect()
        app.ctx.ib = IB()
        await app.ctx.ib.connectAsync('127.0.0.1', 8888, clientId=1)


@app.after_server_stop
def close(app, _):
    app.ctx.ib.disconnect()


# Run App
if __name__ == "__main__":
    # Connect to IB
    # app.ctx.ib = IB()
    # app.ctx.ib.connect('localhost', 8888,clientId=1)
    app.run(port=5000)
