
import traceback
from functools import wraps
from inspect import isawaitable
import sanic.response
from sanic.response import json
from secret_hash import compareSecret


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
                        return await response

                    return response
                else:
                    return json({"status": "not_authorized"}, 403)
            except Exception as e:
                print(traceback.format_exc())
                return json({"status": "not_authorized"}, 403)
        return decorated_function
    return decorator(maybe_func) if maybe_func else decorator
