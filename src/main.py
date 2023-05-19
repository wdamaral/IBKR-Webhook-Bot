# Imports
from sanic import Sanic
from ib_insync import *
from telegram import Bot
from settings import *
from api import bp

# Create Sanicobject called app.
app = Sanic(__name__)
app.config.FORWARDED_SECRET = api_secret
app.ctx.ib = IB()
app.ctx.bot: Bot

app.blueprint(bp)


def main() -> None:
    app.run(host='127.0.0.1', port=5000,
            debug=is_debug, access_log=False)


# Run App
if __name__ == "__main__":
    main()
