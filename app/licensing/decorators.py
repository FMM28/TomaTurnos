from functools import wraps

from flask import current_app


def licensed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        client = current_app.extensions["license_client"]
        client.ensure_licensed()
        return fn(*args, **kwargs)

    return wrapper