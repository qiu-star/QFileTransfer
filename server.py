import socket
import ssl, threading, struct

class Server:
    def __init__(self):
         # generate ssl context
        self.__context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.__context.load_verify_locations('./cer/CA/ca.crt')
        self.__context.load_cert_chain('./cer/server/server.crt', './cer/server/server_rsa_private.pem')
        self.__context.verify_mode = ssl.CERT_REQUIRED
    
    def server_listen(self):
        # listen
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            sock.bind(('127.0.0.1', 9999))
            sock.listen(5)
            with self.__context.wrap_socket(sock, server_side=True) as ssock:
                while True:
                    connection, addr = ssock.accept()
                    print('Connected by: ', addr)
                    thread = threading.Thread(target=self.deal_conn_thread, args=(connection,))
                    thread.start()
    
    def deal_conn_thread(self, connection):
        while True:
            try:
                connection.settimeout(60)
                fileinfo_size = struct.calcsize('1024s')
                buf = connection.recv(fileinfo_size)
                if buf is None:
                    continue
                print(buf)
            except socket.timeout:
                connection.close()
                break
            except ConnectionResetError:
                connection.close()
                break

if __name__ == "__main__":
    server = Server()
    server.server_listen()