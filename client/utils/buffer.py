class RotationBuffer:
    def __init__(self, max_size: int):
        """
        if max_size < 0 then size is unlimited.\n
        if max_size is default then size is MAX_SIZE const
        """

        self.__buf = bytearray()
        self.__max_size = max_size

    def get(self) -> bytes:
        return bytes(self.__buf)

    def extend(self, data: bytes):
        if i := data.rfind(b"\x0c") >= 0:
            print('rfind!!!')
            self.__buf.clear()
            data = data[i:]

        self.__buf.extend(data)

        if 0 <= self.__max_size < len(self.__buf):
            del self.__buf[:self.__max_size]
