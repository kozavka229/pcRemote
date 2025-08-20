import argparse
import asyncio
from getpass import getpass

import aio_pika
import aiormq
import pamqp


def __get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', help="User id")
    parser.add_argument('--room', help="Room id")
    parser.add_argument('--host', default="localhost", help="Server")
    parser.add_argument('--password', default="", dest="password", help="User password")
    parser.add_argument('--port', type=int, default=5672, dest="port", help="Server port")

    args = parser.parse_args()
    if not args.password:
        args.password = getpass()

    args.user = f"user{args.user}"
    args.room = f"room{args.room}"
    return args


__args = __get_args()

CONNECTION_HOST = __args.host
CONNECTION_PORT = __args.port
CONNECTION_LOGIN = __args.user
CONNECTION_PASSWORD = __args.password
CONNECTION_VHOST = __args.room

async def connect() -> tuple[aio_pika.abc.AbstractConnection | None, bool]:
    loop = asyncio.get_running_loop()

    try:
        connection = await aio_pika.connect_robust(
            host=CONNECTION_HOST,
            port=CONNECTION_PORT,
            login=CONNECTION_LOGIN,
            password=CONNECTION_PASSWORD,
            virtualhost=CONNECTION_VHOST,
            loop=loop
        )
        return connection, True
    except pamqp.exceptions.AMQPInternalError:
        print("You havenot permission for this room")
    except aiormq.exceptions.ProbableAuthenticationError:
        print("Invalid password")
    except aiormq.exceptions.AMQPConnectionError:
        print("Connection error")
    return None, False

COMMANDS_QUEUE = "commands"
LOG_QUEUE = "logs"
