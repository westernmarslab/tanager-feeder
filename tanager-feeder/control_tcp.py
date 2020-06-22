import socket
import sys

import socket
import sys
import time

# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.settimeout(3)
# sock.connect(('raspberrypi',12345))
# print('done')

class ControlServer():
    def __init__(self, port):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.hostname=socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)        
        # Bind the socket to the port
        self.server_address = (self.ip_address, port)
#         self.server_address = ('', 12345)
        print('starting up on %s port %s' % self.server_address)
        try:
            self.sock.bind(self.server_address)
        except OSError:
            if 'Only one usage of each socket address' in str(sys.exc_info()):
                print('Warning: multiple attempts to use the same address')
            else:
                print(sys.exc_info())
                raise
        self.queue=[]
        
        
    def listen(self):
        print('TCP server listening.\n\n')
        # Listen for incoming connections
        self.sock.listen(1)
#         for _ in range(10):
#             time.sleep(1)
#             print('sleeping')
        while True:
            # Wait for a connection
            connection, client_address = self.sock.accept()
            
            try:        
                # Receive the data in small chunks and retransmit it
                next_message=b''
                header=connection.recv(6)
                print('header')
                print(header)
                if len(header)!=6:
                    connection.sendall(header)
                else:
                    while len(next_message)<int(header):
                        data = connection.recv(16)
                        next_message+=data
                        if not data:
                            print('WARNING: MESSAGE SHORTER THAN EXPECTED')
                            break
                    self.queue.append(str(next_message, 'utf-8'))
                    connection.sendall(next_message)
            except ConnectionResetError:
                print('CONNECTION RESET')
                self.listen()
            except OSError:
                if 'Only one usage of each socket address' in sys.exc_info()[1]:
                    print('Warning: multiple attempts to use the same address')
                else:
                    print(sys.exc_info())
                    raise
                    
            finally:
                # Clean up the connection
                connection.close()
    
class ControlClient():
    def __init__(self, server_address, base_message, listening_port, timeout=None):
        self.header_len=6 #Needs to match asd-feeder spectrometerserver expected header length on spectrometer computer.
        self.address_info_len=25 #Also needs to match
        
#         message=str(message) #sometimes supplied as bytes
        if not isinstance(base_message, str):
            base_message=base_message.decode('utf-8')
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout!=None:
            self.sock.settimeout(timeout)
        
        # Connect the socket to the port where the server is listening
        self.server_address = server_address
        self.sock.connect(self.server_address)
        
        hostname=socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        header=str(len(base_message))
        while len(header)<self.header_len:
            header='0'+header
        
        address_info=ip_address+'&'+str(listening_port)
        while len(address_info)<self.address_info_len:
            address_info+='&'
        
        full_message=header+address_info+base_message
        if len(full_message)>200:
            print(message)
        full_message=full_message.encode('utf-8')
        
        try: 
            # Send data
            self.sock.sendall(full_message)
        
            # Look for the response
            amount_received = 0
            amount_expected = len(base_message)
            
            self.return_message=''
            while amount_received < amount_expected:
                data = self.sock.recv(10)
                self.return_message+=str(data)
                amount_received += len(data)
                if not data:
                    print('return message was short')
                    print(self.return_message)
                    raise Exception('Full message not returned')

        except ConnectionResetError:
            print('CONNECTION RESET')
            self.__init__(server_address, base_message, listening_port, timeout)
            
            
        finally:
            self.sock.close()
    
        
