def signal_cmd(value: int) -> bytes:
    return f"{COMMAND_SIGNAL}{value}".encode()

def check_signal_command(message: str) -> int | None:
    if message.startswith(COMMAND_SIGNAL):
        signal = message[len(COMMAND_SIGNAL):]
        if signal.isdigit():
            return int(signal)
    return None


COMMAND_SIGNAL = "<SIGN>"
