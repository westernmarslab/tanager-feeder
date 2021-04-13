HEADER_LEN = 12
ADDRESS_LEN = 25  # Number of digits in the address including IP address and port info.

class AlreadyConnectedException(Exception):
    def __init__(self, message="Error: TCP socket is already connected."):
        super().__init__(message)

class ShortMessageError(Exception):
    def __init__(self, message):
        super().__init__(message)

class WrongHeaderError(Exception):
    def __init__(self):
        super().__init__("Wrong header.")

class WrongAddressError(Exception):
    def __init__(self):
        super().__init__("Wrong address returned.")

class NoConfirmationError(Exception):
    def __init__(self):
        super().__init__("No confirmation that message was correct.")