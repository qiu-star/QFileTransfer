import socket
import ssl, time, os, struct, json, tkinter


class Client:
    def __init__(self):
        # generate ssl context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations('./cer/CA/ca.crt')
        context.load_cert_chain('./cer/client/client.crt', './cer/client/client_rsa_private.pem')
        context.verify_mode = ssl.CERT_REQUIRED

        self.__sock = socket.create_connection(('127.0.0.1', 9999))
        self.__ssock = context.wrap_socket(self.__sock, server_hostname='SERVER', server_side=False)

    def send_header(self, header, hformat):
        header_hex = bytes(json.dumps(header).encode('utf-8'))
        fhead = struct.pack(hformat, header_hex)
        self.__ssock.send(fhead)
        print('send over...')

    def send_file(self, file_path):
        file_object = open(file_path, 'rb')
        while True:
            file_data = file_object.read(1024)
            if not file_data:
                break
            self.__ssock.send(file_data)
        file_object.close()

    def receive_header(self, hformat):
        header_size = struct.calcsize(hformat)
        buf = self.__ssock.recv(header_size)
        if not buf:
            return None
        header_json = str(struct.unpack(hformat, buf)[0], encoding='utf-8').strip('\00')
        header = json.loads(header_json)
        return header

    def receive_file(self, file_size, file_path):
        print('file name: %s, filesize: %s' % (file_path, file_size))
        recvd_size = 0
        file = open(file_path, 'wb')
        print('start receiving...')
        while not recvd_size == file_size:
            if file_size - recvd_size > 1024:
                rdata = self.__ssock.recv(1024)
                recvd_size += len(rdata)
            else:
                rdata = self.__ssock.recv(file_size - recvd_size)
                recvd_size = file_size
            file.write(rdata)
        file.close()
        print('receive done')

    def login(self, username, password):
        header = {
            'Command': 'Login',
            'fileName': '',
            'fileSize': '',
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'user': username,
            'password': password,
        }
        self.send_header(header, '1024s')
        # wait for the server answer
        header = self.receive_header('128s')
        if not header:
            return False
        # from the server answer, we will know whether login successfully or not
        stat = header['stat']
        if stat != 'Success':
            return False
        # recieve the file name the user upload on the server
        file_info_list = self.receive_header('1024s')
        print(file_info_list)  # @TODO: show the file name on GUI
        return True

    def logout(self, username, password):
        header = {
            'Command': 'Logout',
            'fileName': '',
            'fileSize': '',
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'user': username,
            'password': password
        }
        self.send_header(header, '1024s')
        # wait for the server answer
        header = self.receive_header('128s')
        if not header:
            return
        if header['stat'] != 'Success':
            return
        self.__ssock.close()

    def register(self, username, password):
        header = {
            'Command': 'Register',
            'fileName': '',
            'fileSize': '',
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'user': username,
            'password': password,
        }
        self.send_header(header, '1024s')
        header = self.receive_header('128s')
        if not header:
            return False
        stat = header['stat']
        if stat == 'Success':
            return True
        else:
            return False

    def upload(self, file_path, username):
        # check whether the file exists
        if not os.path.isfile(file_path):
            print("The File doesn't exists!")
            return
        # send header
        header = {
            'Command': 'Upload',
            'fileName': os.path.basename(file_path),
            'fileSize': os.stat(file_path).st_size,
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'user': username,
            'downloadFilename': '',
            'cookie': ''
        }
        self.send_header(header, '1024s')
        # send file
        self.send_file(file_path)

    def download(self, file_name, username, password):
        header = {
            'Command': 'Download',
            'fileName': file_name,
            'fileSize': '',
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'user': username,
            'password': password
        }
        self.send_header(header, '1024s')
        response = self.receive_header('128s')
        if not response:
            return False
        if response['stat'] != 'Success':
            return False
        file_path = os.path.join('./client_download', file_name)
        self.receive_file(response['fileSize'], file_path)
        return True

    def get_file_info_list(self, username):
        header = {
            'Command': 'Update',
            'fileName': '',
            'fileSize': '',
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'user': username
        }
        self.send_header(header, '1024s')
        file_info_list = self.receive_header('1024s')
        print(file_info_list)

    def delete_file(self, username, password, file_name):
        header = {
            'Command': 'DeleteFile',
            'fileName': file_name,
            'fileSize': '',
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'user': username,
            'password': password
        }
        self.send_header(header, '1024s')
        response = self.receive_header('128s')
        if not response:
            return False
        if response['stat'] != 'Success':
            return False
        return True


if __name__ == "__main__":
    client = Client()
    # client.register("qiu", "123")
    client.login("qiu", "123")  # login succ
    # client.login("qiu", "12")   # login fail
    # client.upload("doc/1.txt", "qiu")
    # client.download("1.png", "qiu", "12") # login fail
    # client.download("1.md", "qiu", "123") # no such file
    # client.download("1.png", "qiu", "123") # success
    # client.get_file_info_list("qiu")
    # client.logout("qiu", "123")
    # client.delete_file("qiu", "12", "1.txt") # login fail
    # client.delete_file("qiu", "123", "1.txt") # success
    # client.delete_file("qiu", "123", "1.txt") # no such file
