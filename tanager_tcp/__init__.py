import socket
from typing import Optional, Tuple

global HEADER_LEN
HEADER_LEN = 12
global ADDRESS_LEN
ADDRESS_LEN = 25  # Number of digits in the address including IP address and port info.


class TanagerServer:
    def __init__(self, port: int):  # Port is the port to listen on
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        # Bind the socket to the port
        self.server_address = (ip_address, port)
        # self.server_address = ("", port)

        self.sock.bind(self.server_address)
        self.queue = []
        self.remote_server_address = None

    def listen(self):
        print(f"Listening on {self.server_address[0]} port {self.server_address[1]}.\n\n")
        # Listen for incoming connections
        self.sock.listen(1)
        # Wait for a connection

        while True:
            connection, _ = self.sock.accept()
            try:
                # Receive the header telling the length of the message
                header = b""
                remaining_len = HEADER_LEN - len(header)
                while remaining_len > 0:
                    next_message = connection.recv(remaining_len)
                    header += next_message
                    remaining_len = HEADER_LEN - len(header)
                    if not next_message:
                        raise ShortMessageError("Message does not contain full header.")

                # Receive the address where the remote computer will be listening for other messages
                remote_server_address = b""
                remaining_len = ADDRESS_LEN - len(remote_server_address)
                while remaining_len > 0:
                    next_message = connection.recv(remaining_len)
                    remote_server_address += next_message
                    remaining_len = ADDRESS_LEN - len(remote_server_address)
                    if not next_message:
                        raise ShortMessageError("Message does not include full address of remote computer.")

                decoded_remote_server_address = remote_server_address.decode("utf-8").split("&")
                self.remote_server_address = (decoded_remote_server_address[0], int(decoded_remote_server_address[1]))

                # Receive the actual message
                message = b""
                while len(message) < int(header):
                    data = connection.recv(1024)
                    message += data
                    if not data:
                        raise ShortMessageError("Message shorter than expected")

                self.queue.append(str(message, "utf-8"))

                # Send a return message containing the header and address info
                connection.sendall(header + remote_server_address)

            except (ConnectionResetError, ConnectionAbortedError, ShortMessageError):  # Happens on restart of other computer
                self.listen()
            finally:
                connection.close()


class TanagerClient:
    # Server address is where you will send your message, listening port is the port you have a server
    # listening for additional messages on.
    def __init__(self, server_address: Optional[Tuple[str, int]], listening_port: int, timeout=None):
        self.server_address = server_address
        self.listening_port = listening_port
        self.sock = None

        # Create a TCP/IP socket

        self.connected = False

    def connect(self, timeout: float = 5) -> bool:
        if self.connected:
            raise AlreadyConnectedException
        if self.server_address is None:
            return False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        # Connect the socket to the port where the server is listening
        try:
            self.sock.connect(self.server_address)
            self.connected = True
            return True
        except (socket.timeout, socket.gaierror, TimeoutError, ConnectionRefusedError, OSError):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connected = False
            return False

    def send(self, base_message: str) -> bool:
        if not self.connected:
            self.connect()
        if not self.connected:
            return False
        # base message may be passed as string or bytes-like object
        if isinstance(base_message, (bytes, bytearray)):
            print("Message passed as bytes")
            base_message = base_message.decode("utf-8")

        # Make sure the header is the right length
        header = str(len(base_message))
        while len(header) < HEADER_LEN:
            header = "0" + header

        # Get address info to send with message
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        address_info = ip_address + "&" + str(self.listening_port)
        while len(address_info) < ADDRESS_LEN:
            address_info += "&"

        # Concatenate various parts of the message and convert to bytes
        full_message = header + address_info + base_message
        full_message = full_message.encode("utf-8")

        try:
            # Send data
            self.sock.sendall(full_message)

            # Look for the response
            next_message = self.sock.recv(HEADER_LEN + ADDRESS_LEN)
            return_message = b""
            while next_message:
                return_message += next_message
                next_message = self.sock.recv(
                    HEADER_LEN + ADDRESS_LEN
                )  # If all is as expected, should be b''. If full message didn't make
                # it through in first sock.recv could have content.
                if len(return_message) > HEADER_LEN + ADDRESS_LEN:
                    raise ShortMessageError

            # Check that the remote server received the correct message length
            return_header = return_message[0:HEADER_LEN].decode("utf-8")
            if return_header != header:
                raise WrongHeaderError

            # Check that the remote server received the address to listen on
            return_address = return_message[HEADER_LEN:].decode("utf-8")
            if return_address != address_info:
                raise WrongAddressError
        except (OSError, WrongHeaderError, WrongAddressError):
            print("self.sock is not a socket, or server address is invalid argument? Retrying.")
            self.connected = False
            return self.send(base_message)

        except ConnectionResetError:  # Happens when one computer is restarted.
            print("Connection reset.")
            self.connected = False
            return self.send(base_message)

        except (socket.timeout, socket.gaierror, TimeoutError):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return False
        finally:
            self.connected = False
            self.sock.close()

        return True

    def close(self):
        self.sock.close()


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