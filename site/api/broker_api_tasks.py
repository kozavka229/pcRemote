import json
import os
from typing import Literal

from celery import shared_task, signals
import requests
from loguru import logger
import os.path as path
from urllib.parse import quote

METHOD = Literal["get", "put", "delete", "post"]

API_BROKER_URL = os.getenv("API_BROKER_URL")
if API_BROKER_URL is None:
    logger.error("API_BROKER_URL not set")

__session = requests.Session()
__session.auth = (os.getenv("API_BROKER_ADMIN_USERNAME"), os.getenv("API_BROKER_ADMIN_PASSWORD"))
__session.headers.update({"Content-Type": "application/json"})
__close_session = signals.worker_shutdown.connect(lambda *_, **__: __session.close())


def __api(target):
    def endpoint(method: METHOD, *points: str, data: dict = None) -> dict:
        url = path.join(API_BROKER_URL, target, *map(quote, points))

        response = getattr(__session, method.lower())(url=url, data=json.dumps(data))
        if response.status_code not in (201, 204):
            logger.error(f"{url} {response.status_code} {response.text}")

        return {"status": response.status_code, "text": response.text}

    return endpoint

__vhosts = __api("vhosts")
__users = __api("users")
__permissions = __api("permissions")


@shared_task
def create_vhost(vhost_id: int, data: dict = None):
    return __vhosts("put", vhost(vhost_id), data=data)

@shared_task
def delete_vhost(vhost_id: int):
    return __vhosts("delete", vhost(vhost_id))


@shared_task
def create_user(user_id: int, password: str, tag: str = ""):
    return __users("put", user(user_id), data={"password": password, "tags": tag})

@shared_task
def delete_user(user_id: int,):
    return __users("delete", user(user_id))

@shared_task
def set_permission(vhost_id: int, user_id: int, configure: str = ".*", write: str = ".*", read: str = ".*"):
    return __permissions("put", vhost(vhost_id), user(user_id), data={"configure": configure, "write": write, "read": read})

@shared_task
def delete_permission(vhost_id: int, user_id: int):
    return __permissions("delete", vhost(vhost_id), user(user_id))

@shared_task
def create_vhost_and_set_permission(vhost_id: int, user_id: int, configure: str = ".*", write: str = ".*", read: str = ".*"):
    return create_vhost(vhost_id), set_permission(vhost_id, user_id, configure, write, read)

def vhost(n: int) -> str:
    return f"room{n}"

def user(n: int) -> str:
    return f"user{n}"
