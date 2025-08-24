import asyncio
from collections.abc import Callable, Awaitable

import aio_pika
import aiormq
import pamqp
from aio_pika import Message
from aio_pika.abc import AbstractChannel, AbstractQueue, AbstractIncomingMessage, AbstractConnection

from .api import API
from .logger import log
from client import config


async def produce(channel: AbstractChannel, queue_name: str, data: bytes):
    log("send: ".encode() + data)
    await channel.default_exchange.publish(Message(data), queue_name)

async def consume(queue: AbstractQueue, log_hook: Callable[[bytes], Awaitable[None]]):
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            message: AbstractIncomingMessage
            async with message.process():
                log("get: ".encode() + message.body)
                await log_hook(message.body)


def _make_url(room: str):
    with API(config.API_URL, (config.USER, config.PASSWORD)) as api:
        login = api.apiuser()
        room = api.apiroom(room)

    return aio_pika.connection.make_url(
        host=config.CONN_HOST,
        port=config.CONN_PORT,
        login=login,
        password=config.PASSWORD,
        virtualhost=room,
    )

async def connect(room: str) -> tuple[AbstractConnection | None, bool]:
    loop = asyncio.get_running_loop()

    try:
        connection = await aio_pika.connect_robust(_make_url(room), loop=loop)
        return connection, True
    except pamqp.exceptions.AMQPInternalError:
        print("You havenot permission for this room")
    except aiormq.exceptions.ProbableAuthenticationError:
        print("Invalid password")
    except aiormq.exceptions.AMQPConnectionError:
        print("Connection error")
    return None, False
