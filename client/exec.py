import asyncio
import asyncio.subprocess as asubprocess
from asyncio import Task

import aio_pika
import config
import commands

PRODUCER_QUEUE = "logs"
CONSUMER_QUEUE = "commands"

class CommandExecutor:
    def __init__(self, channel):
        self.__channel = channel
        self.__proc: asubprocess.Process | None = None
        self.__task: Task | None = None

    @property
    def executed(self):
        return self.__proc is not None

    async def execute(self, command: str):
        if self.executed:
            await self.log(f"\n\nERROR: Cannot execute \"{command}\" because executing another command\n\n\n".encode())
            return

        self.__task = asyncio.create_task(self.__execute_loop(command))

    async def __execute_loop(self, command: str):
        print("execute:", command)
        self.__proc = await asubprocess.create_subprocess_shell(command, stdin=asubprocess.PIPE,
                                                                stdout=asubprocess.PIPE, stderr=asubprocess.STDOUT)

        while self.__proc.returncode is None:
            output = await self.__proc.stdout.read(1024)
            await self.log(output)
            print(output)

        self.__proc = None

    async def log(self, message: bytes):
        await self.__channel.default_exchange.publish(
            aio_pika.Message(message),
            routing_key=PRODUCER_QUEUE
        )

    def send_signal(self, signal):
        if not self.executed:
            return

        self.__proc.send_signal(signal)

async def producer(channel: aio_pika.abc.AbstractChannel):
    await channel.declare_queue(PRODUCER_QUEUE)

async def consumer(channel: aio_pika.abc.AbstractChannel):
    queue = await channel.declare_queue(CONSUMER_QUEUE)
    async with queue.iterator() as queue_iter:
        print("Wait commands...")

        executor = CommandExecutor(channel)

        async for message in queue_iter:
            async with message.process():
                msg = message.body.decode()

                if (signal := commands.check_signal_command(msg)) is not None:
                    print("send signal")
                    executor.send_signal(signal)
                    continue

                await executor.execute(msg)

async def main():
    connection, connected = await config.connect()
    if not connected:
        return

    async with connection:
        channel = await connection.channel()

        await asyncio.gather(consumer(channel), producer(channel))


if __name__ == "__main__":
    asyncio.run(main())
