import asyncio
import os
import pty
import signal
import sys

from aio_pika.abc import AbstractChannel

from utils import colorize, COLOR, short_pika, logger, const
from utils.buffer import RotationBuffer
import config

PRODUCER_QUEUE = const.LOG_QUEUE
CONSUMER_QUEUE = const.COMMANDS_QUEUE


class Executor:
    def __init__(self, buffer_max_size: int):
        self.__child_pid = None
        self.__fd = None
        self.__running = False
        self.__buffer = RotationBuffer(max_size=buffer_max_size)

    @property
    def is_running(self) -> bool:
        return self.__running

    @property
    def buffer(self) -> bytes:
        return self.__buffer.get()

    def setup(self):
        if None not in (self.__child_pid, self.__fd):
            raise RuntimeError("Double setup")

        child_pid, fd = pty.fork()

        if child_pid == 0:
            os.execvp("bash", ["bash"])
        else:
            self.__child_pid = child_pid
            self.__fd = fd
            self.__running = True

    def send(self, data: str | bytes):
        if isinstance(data, str):
            data = data.encode()

        try:
            os.write(self.__fd, data)
            sys.stdin.flush()
        except OSError as e:
            self.__running = False
            raise e

    def read(self, length: int) -> bytes:
        sys.stdout.flush()

        try:
            data = os.read(self.__fd, length)
            self.__buffer.extend(data)
            return data
        except OSError as e:
            self.__running = False
            raise e

    def close(self):
        if self.__running:
            os.kill(self.__child_pid, signal.SIGKILL)
            os.close(self.__fd)
            os.waitpid(self.__child_pid, 0)

            self.__running = False
            self.__fd = None
            self.__child_pid = None

    def __aenter__(self):
        return self

    def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()

class ProducerExecutor:
    def __init__(self, channel: AbstractChannel, queue_name: str, bytes_read: int, buffer_max_size: int):
        super().__init__()

        self.__channel = channel
        self.__queue_name = queue_name
        self.__bytes_read = bytes_read

        self.__executor = Executor(buffer_max_size=buffer_max_size)

    async def setup(self):
        self.__executor.setup()
        await self.log(const.PING)
        await self.log_fd(self.__bytes_read)

    async def send(self, data: bytes):
        if data == const.PING:
            await self.log(const.PONG)
            await self.log(self.__executor.buffer)
            return

        await asyncio.to_thread(self.__executor.send, data)
        sys.stdin.flush()

    async def log(self, data: bytes):
        await short_pika.produce(self.__channel, self.__queue_name, data)

    async def log_fd(self, length: int):
        try:
            data = await asyncio.to_thread(self.__executor.read, length)
        except OSError:
            pass
        else:
            await self.log(data)

    async def log_loop(self):
        print(colorize("Running...", color=COLOR.OKGREEN))
        while self.__executor.is_running:
            await self.log_fd(self.__bytes_read)

        await self.exit()
        print(colorize("Stopped", color=COLOR.WARNING))

    async def exit(self):
        await asyncio.to_thread(self.__executor.close)

        if not self.__channel.is_closed:
            await self.log(const.EXIT)
            await self.__channel.close()

    async def __aenter__(self):
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit()


async def main():
    try:
        room = sys.argv[1]
    except IndexError:
        print("Enter room name for connect")
        return

    connection, connected = await short_pika.connect(room)
    if not connected:
        return

    async with connection:
        channel = await connection.channel()

        cq = await channel.declare_queue(CONSUMER_QUEUE)
        await cq.purge()

        async with ProducerExecutor(channel, PRODUCER_QUEUE, const.BYTES_READ, const.BUFFER_MAX_SIZE) as executor:
            await asyncio.gather(short_pika.consume(cq, executor.send), executor.log_loop())


if __name__ == "__main__":
    if config.LOG:
        logger.setfile('exec.log')

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
