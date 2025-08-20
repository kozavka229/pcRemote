import asyncio

import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue

from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea

import config


class Sender:
    PRODUCER_QUEUE = config.COMMANDS_QUEUE
    CONSUMER_QUEUE = config.LOG_QUEUE

    def __init__(self):
        self.__conn: AbstractConnection | None = None
        self.__channel: AbstractChannel | None = None
        self.__consumer_queue: AbstractQueue | None = None

    @property
    def connection(self) -> AbstractConnection:
        return self.__conn

    @property
    def channel(self) -> AbstractChannel:
        return self.__channel

    async def setup(self) -> bool:
        self.__conn, connected = await config.connect()
        if not connected:
            return False

        self.__channel = await self.__conn.channel()
        await self.__channel.declare_queue(self.PRODUCER_QUEUE)
        self.__consumer_queue = await self.__channel.declare_queue(self.CONSUMER_QUEUE)
        self.log("Connected\n")
        return True

    async def execute(self, text: str):
        await self.__publish(text.encode())

    async def consume(self):
        async with self.__consumer_queue.iterator() as queue_iter:

            async for message in queue_iter:
                message: aio_pika.abc.AbstractIncomingMessage
                async with message.process():
                    self.log(message.body.decode())

    def log(self, message: str):
        print(message, end="")

    async def __publish(self, message: bytes):
        await self.__channel.default_exchange.publish(aio_pika.Message(message), routing_key=self.PRODUCER_QUEUE)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__conn.close()


class ApplicationLogSender(Sender):
    def __init__(self):
        super().__init__()

        output_field = TextArea(style="class:output-field")
        input_field = TextArea(height=1, prompt=">>> ", style="class:input-field", multiline=False, wrap_lines=False)

        container = HSplit([output_field, Window(height=1, char="-", style="class:line"), input_field])

        input_field.accept_handler = self.__input_accept_handler

        kb = KeyBindings()

        @kb.add("c-q")
        def _(event):
            """ Pressing Ctrl-Q will exit the user interface. """
            event.app.exit()
            asyncio.create_task(self.connection.close())

        style = Style(
            [
                ("output-field", "bg:#000044 #ffffff"),
                ("input-field", "bg:#000000 #ffffff"),
                ("line", "#004400"),
            ]
        )

        self.__app = Application(
            layout=Layout(container, focused_element=input_field),
            key_bindings=kb,
            style=style,
            mouse_support=True,
            full_screen=True,
        )
        self.__outbuff = output_field.buffer
        self.__inbuff = input_field.buffer

    def log(self, message: str):
        new_text = self.__outbuff.text + message
        self.__outbuff.document = Document(text=new_text, cursor_position=len(new_text))

    def __input_accept_handler(self, _):
        command = self.__inbuff.text
        self.log("\n>>> " + command + "\n")
        asyncio.create_task(self.execute(command))

    async def run(self):
        await self.__app.run_async()


async def main():
    async with ApplicationLogSender() as sender:
        if not await sender.setup():
            return

        await asyncio.gather(sender.consume(), sender.run())


if __name__ == "__main__":
    asyncio.run(main())
