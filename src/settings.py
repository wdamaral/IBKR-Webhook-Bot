from decouple import config

alert_secret_key = config('ALERT_SECRET_KEY', cast=str, default=None)
admin_secret_key = config('ADMIN_SECRET_KEY', cast=str, default=None)
enable_telegram = config('ENABLE_TELEGRAM', default=False, cast=bool)
telegram_token = config('TELEGRAM_TOKEN', default=None)
channel_id = config('CHANNEL_ID', cast=int)
ib_host = config('IB_HOST', default=None)
ib_port = config('IB_PORT', cast=int)
is_debug = config('DEBUG', cast=bool, default=True)
internal_portal = config('INTERNAL_PORTAL', default=None)
api_secret = config('API_SECRET', default=None)
