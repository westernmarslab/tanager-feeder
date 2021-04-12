import os
import socket
import time
from typing import Optional, Tuple
from tanager_tcp.utils import *

class TanagerServer:
    def __init__(self, port: int, wait_for_network=False):  # Port is the port to listen on
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(hostname)

        #This is useful because when the spectrometer computer starts up, asd-feeder may start
        # before network connections are initialized. This can lead to the TanagerServer using localhost.
        if wait_for_network:
            while self.ip_address[0:3] == "127":
                print("Waiting for network connection...")
                hostname = socket.gethostname()
                self.ip_address = socket.gethostbyname(hostname)
                time.sleep(2)

        # Bind the socket to the port
        # self.server_address = (ip_address, port) #This causes the raspberry pi to fail.
        self.server_address = ("", port)

        self.sock.bind(self.server_address)
        self.queue = []
        self.remote_server_address = None

    def listen(self):
        print(f"Listening on {self.ip_address} port {self.server_address[1]}.\n\n")
        # Listen for incoming connections
        self.sock.listen(1)
        # Wait for a connection
        i = 0
        while True:
            i += 1

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



                # Send a return message containing the header and address info
                connection.sendall(header + remote_server_address)

                # Look for the response
                timeout = 3
                confirmation_message = b""
                while not confirmation_message and timeout > 0:
                    next_message = connection.recv(7)
                    time.sleep(1)
                    timeout -= 1
                    while next_message:
                        confirmation_message += next_message
                        next_message = connection.recv(7)  # If all is as expected, should be b''. If full message didn't make
                        # it through in first sock.recv could have content.

                if confirmation_message.decode("utf-8") != "Correct":
                    with open(os.path.join(os.path.expanduser("~"), ".noconfirm"), "w+"):
                        pass
                    print(confirmation_message)
                    raise NoConfirmationError

                self.queue.append(str(message, "utf-8"))

            except (ConnectionResetError, ConnectionAbortedError, ShortMessageError, NoConfirmationError):  # Happens on restart of other computer
                print("Error receiving message. Restarting.\n")
                self.listen()

            finally:
                connection.close()
