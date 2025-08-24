import asyncio
import sys
import termios
import tty

import readchar
from aio_pika.abc import AbstractConnection, AbstractChannel

from utils import logger, short_pika, const
from utils import colorize, COLOR
import config

EXIT_KEY = readchar.key.CTRL_L


PRODUCER_QUEUE = const.COMMANDS_QUEUE
CONSUMER_QUEUE = const.LOG_QUEUE

readchar.config.INTERRUPT_KEYS = []


class Producer:
    def __init__(self, channel: AbstractChannel, queue_name: str, simple_input_mode: bool = False):
        self.__channel = channel
        self.__queue_name = queue_name
        self.__simple_input_mode = simple_input_mode

    async def loop(self):
        try:
            tty.setcbreak(sys.stdin.fileno())
        except termios.error as e:
            print(f"{type(e)}: {e}")
            print("Enabled simple input mode")
            self.__simple_input_mode = True

        await self.produce(const.PING)

        while True:
            inp: str = await self.getinput()
            if inp == EXIT_KEY:
                break

            await self.produce(inp.encode())

        await self.__channel.close()
        print('close')

    async def getinput(self) -> str:
        if self.__simple_input_mode:
            return await asyncio.to_thread(input) or '\n'
        else:
            return await asyncio.to_thread(readchar.readchar)

    async def produce(self, data: bytes):
        await short_pika.produce(self.__channel, self.__queue_name, data)


async def log(message: bytes):
    cprint = lambda *args, color: print(colorize(*args, color=color))

    if message == const.EXIT:
        cprint('\n# Executer is down\n', color=COLOR.WARNING)

    elif message == const.PING:
        cprint('# Executer start\n', color=COLOR.OKGREEN)

    elif message == const.PONG:
        cprint('# Executer is running\n', color=COLOR.OKCYAN)

    else:
        print(message.decode(), end='')
        sys.stdout.flush()


async def main():
    try:
        room = sys.argv[1]
    except IndexError:
        print("Enter room name for connect")
        return

    connection, connected = await short_pika.connect(room)
    if not connected:
        return

    connection: AbstractConnection
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(PRODUCER_QUEUE)

        prod = Producer(channel, PRODUCER_QUEUE)
        cq = await channel.declare_queue(CONSUMER_QUEUE)
        await cq.purge()

        print('Wait executor...')
        await asyncio.gather(short_pika.consume(cq, log), prod.loop())


if __name__ == "__main__":
    if config.LOG:
        logger.setfile('send.log')

    try:
        print('Press CTRL+L for exit\n')
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        logger.closefile()
