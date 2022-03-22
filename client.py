import socket
import ssl,time,os,struct,json,tkinter

class Client:
    def __init__(self):
        # generate ssl context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations('./cer/CA/ca.crt')
        context.load_cert_chain('./cer/client/client.crt', './cer/client/client_rsa_private.pem')
        context.verify_mode = ssl.CERT_REQUIRED

        self.__sock = socket.create_connection(('127.0.0.1', 9999))
        self.__ssock = context.wrap_socket(self.__sock, server_hostname='SERVER', server_side=False)
    
    def send(self):
        text = "Hello World!\n"
        buf = struct.pack('1024s', bytes(text.encode('utf-8')))
        self.__ssock.send(buf)

if __name__ == "__main__":
    client = Client()
    client.send()