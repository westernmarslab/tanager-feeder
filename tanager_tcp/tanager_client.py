import os
import socket
import time
from typing import Optional, Tuple
from tanager_tcp.utils import *

class TanagerClient:
    # Server address is where you will send your message, listening port is the port you have a server
    # listening for additional messages on.
    def __init__(self, server_address: Optional[Tuple[str, int]], listening_port: int, timeout=None):
        self.server_address = server_address
        self.listening_port = listening_port
        self.sock = None
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
            return_message = self.sock.recv(HEADER_LEN + ADDRESS_LEN)

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

            # Send a confirmation that everything went through correctly.
            self.sock.sendall("Correct".encode("utf-8"))

        except OSError:
            import traceback
            traceback.print_exc()
            print("TCP OSError. Retrying.")
            self.connected = False
            return self.send(base_message)
        except (WrongHeaderError, WrongAddressError):
            print("Wrong TCP header information returned. Retrying.")
            self.sock.sendall("Wrong Header".encode("utf-8"))
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