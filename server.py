import socket
import ssl, threading, struct, json, os, pymysql


class Server:
    def __init__(self):
        # open DB
        self.__db = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='ql782134193', db='fileTransfer', charset='utf8')
        self.__cursor = self.__db.cursor()
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

    def send_header(self, connection, header, hformat):
        header_hex = bytes(json.dumps(header).encode('utf-8'))
        fhead = struct.pack(hformat, header_hex)
        connection.send(fhead)
        print('send over...')

    def send_file(self, connection, file_path):
        file_object = open(file_path, 'rb')
        while True:
            file_data = file_object.read(1024)
            if not file_data:
                break
            connection.send(file_data)
        file_object.close()

    def receive_file(self, connection, file_size, file_name):
        print('file name: %s, filesize: %s' % (file_name, file_size))
        recvd_size = 0
        file = open(file_name, 'wb')
        print('start receiving...')
        while not recvd_size == file_size:
            if file_size - recvd_size > 1024:
                rdata = connection.recv(1024)
                recvd_size += len(rdata)
            else:
                rdata = connection.recv(file_size - recvd_size)
                recvd_size = file_size
            file.write(rdata)
        file.close()
        print('receive done')

    def write_log(self, log_txt):
        with open('./server_file_info/server_log.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(log_txt)

    def write_file_catalogue(self, file_info):
        with open('./server_file_info/file_catalogue.txt', 'a', encoding='utf-8') as file_catalogue:
            file_catalogue.write(file_info)

    def file_size_to_text(self, file_size):
        if file_size < 1024:
            return "%s bytes" % (file_size)
        elif file_size/1024 < 1024:
            return "%.2f Kb" % (file_size/1024)
        elif (file_size/1024)/1024 < 1024:
            return "%.2f Mb" % ((file_size/1024)/1024)
        else:
            return "%.2f Gb" % (((file_size/1024)/1024)/1024)

    def login_succ(self, connection, username):
        # when client login successfully, server will send the filenames on the server to the client
        file_catalogue = './server_file_info/file_catalogue.txt'
        header = {
            'Feedback': 'Login',
            'stat': 'Success',
            'fileSize': os.stat(file_catalogue).st_size,
            'user': username
        }
        self.send_header(connection, header, '128s')
        # send the filenames on the server to the client
        self.send_file(connection, file_catalogue)

    def login_fail(self, connection, username):
        header = {
            'Feedback': 'Login',
            'stat': 'Fail',
            'fileSize': '',
            'user': username
        }
        self.send_header(connection, header, '128s')

    def login(self, connection, header):
        username = header['user']
        password = header['password']
        time = header['time']
        # check whether the user and password is correct
        sql = "select * from user where username = '%s' and password = '%s'" % (username,password)
        self.__cursor.execute(sql)
        data = self.__cursor.fetchone()
        login_log = ""
        if data:
            self.login_succ(connection, username)
            login_log = '\n%s try to login at "%s" , Stat: Success ' % (username, time)
        else:
            self.login_fail(connection, username)
            login_log = '\n%s try to login at "%s" , Stat: Fail ' % (username, time)
        # write log
        self.write_log(login_log)

    def register_succ(self, connection, username, password, time):
        sql = "insert into user values ('%s','%s','%s')" % (username, password, time)
        self.__cursor.execute(sql)
        self.__db.commit()
        header = {
            'Feedback': 'Register',
            'stat': 'Success',
            'fileSize': '',
            'user': username
        }
        self.send_header(connection, header, '128s')

    def register_fail(self, connection, username):
        header = {
            'Feedback': 'Register',
            'stat': 'Exist',
            'fileSize': '',
            'user': username
        }
        self.send_header(connection, header, '128s')

    def register(self, connection, header):
        username = header['user']
        password = header['password']
        time = header['time']
        # check whether the user has exists
        sql = "select * from user where username = '%s'" % (username)
        self.__cursor.execute(sql)
        data = self.__cursor.fetchone()
        register_log = ""
        if data:
            # user exists
            self.register_fail(connection, username)
            register_log = '\n%s try to register at "%s" , Stat: Fail ' % (username, time)
        else:
            self.register_succ(connection, username, password, time)
            register_log = '\n%s try to register at "%s" , Stat: Success ' % (username, time)
        self.write_log(register_log)

    def upload(self, connection, header):
        file_name = header['fileName']
        file_size = header['fileSize']
        time = header['time']
        user = header['user']
        file_path = os.path.join('./server_file_storage/', file_name)
        self.receive_file(connection, file_size, file_path)

        file_size_str = self.file_size_to_text(int(file_size))
        new_file_info = '{"文件名": "%s", "上传者": "%s", "上传时间": "%s", "大小": "%s"}\n' % (file_name, user, time, file_size_str)
        self.write_file_catalogue(new_file_info)

        upload_log = '\n%s upload a file "%s" at %s' % (user, file_name, time)
        self.write_log(upload_log)

    def do_command(self, connection, header):
        command = header['Command']
        if command == 'Login':
            self.login(connection, header)
        elif command == 'Register':
            self.register(connection, header)
        elif command == 'Upload':
            self.upload(connection, header)
        elif command == 'Download':
            print('Download')
        elif command == 'DeleteFile':
            print('DeleteFile')
        elif command == 'DeleteUser':
            print('DeleteUser')

    def deal_conn_thread(self, connection):
        while True:
            try:
                connection.settimeout(60)
                fileinfo_size = struct.calcsize('1024s')
                buf = connection.recv(fileinfo_size)
                if not buf:
                    continue
                header_json = str(struct.unpack('1024s', buf)[0], encoding='utf-8').strip('\00')
                header = json.loads(header_json)
                self.do_command(connection, header)
            except socket.timeout:
                connection.close()
                break
            except ConnectionResetError:
                connection.close()
                break


if __name__ == "__main__":
    server = Server()
    server.server_listen()