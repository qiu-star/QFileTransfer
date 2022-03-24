import socket
import ssl, threading, struct, json, os, pymysql


class Server:
    def __init__(self):
        # open DB
        self.__db = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='ql782134193', db='fileTransfer', charset='utf8')
        self.__cursor = self.__db.cursor(pymysql.cursors.DictCursor)
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

    def file_size_to_text(self, file_size):
        if file_size < 1024:
            return "%s bytes" % (file_size)
        elif file_size/1024 < 1024:
            return "%.2f Kb" % (file_size/1024)
        elif (file_size/1024)/1024 < 1024:
            return "%.2f Mb" % ((file_size/1024)/1024)
        else:
            return "%.2f Gb" % (((file_size/1024)/1024)/1024)

    def check_user_password(self, username, password):
        sql = "select * from user where username = '%s' and password = '%s'" % (username, password)
        self.__cursor.execute(sql)
        data = self.__cursor.fetchone()
        if data:
            return True
        return False

    def get_file_info_uploaded_by_user(self, username, filename):
        sql = "select * from fileinfo where username = '%s' and filename = '%s'" % (username, filename)
        self.__cursor.execute(sql)
        file_info = self.__cursor.fetchone()
        return file_info

    def login_succ(self, connection, username):
        # when client login successfully, server will send the filenames on the server to the client
        header = {
            'Feedback': 'Login',
            'stat': 'Success',
            'fileSize': '',
            'user': username
        }
        self.send_header(connection, header, '128s')
        # send the filenames which the user upload on the server to the client
        sql = "select filename, upload_time, size from fileinfo where username = '%s'" % (username)
        self.__cursor.execute(sql)
        data = self.__cursor.fetchall()
        self.send_header(connection, data, '1024s')

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
        login_log = ""
        if self.check_user_password(username, password):
            self.login_succ(connection, username)
            login_log = '\n%s try to login at "%s" , Stat: Success ' % (username, time)
        else:
            self.login_fail(connection, username)
            login_log = '\n%s try to login at "%s" , Stat: Fail ' % (username, time)
        # write log
        self.write_log(login_log)

    def logout(self, connection, header):
        username = header['user']
        password = header['password']
        time = header['time']
        logout_log = ""
        if self.check_user_password(username, password):
            header = {
                'Feedback': 'Login',
                'stat': 'Success',
                'fileSize': '',
                'user': username
            }
            self.send_header(connection, header, '128s')
            connection.settimeout(60)
            connection.close()
            logout_log = '\n%s try to logout at "%s" , Stat: Success ' % (username, time)
        else:
            header = {
                'Feedback': 'Logout',
                'stat': 'Fail',
                'fileSize': '',
                'user': username
            }
            self.send_header(connection, header, '128s')
            logout_log = '\n%s try to logout at "%s" , Stat: Fail ' % (username, time)
        self.write_log(logout_log)

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
        file_path = os.path.join('./server_file_storage/', user+file_name)
        self.receive_file(connection, file_size, file_path)

        # add new file upload record
        file_size_str = self.file_size_to_text(int(file_size))
        sql = "insert into fileinfo values ('%s','%s','%s','%s','%s')" % (file_name, file_path, time, user, file_size_str)
        self.__cursor.execute(sql)
        self.__db.commit()

        upload_log = '\n%s upload a file "%s" at %s' % (user, file_name, time)
        self.write_log(upload_log)

    def download(self, connection, header):
        username = header['user']
        password = header['password']
        time = header['time']
        filename = header['fileName']
        download_log = ''

        if self.check_user_password(username, password):
            # check whether the user has uploaded the file
            file_info = self.get_file_info_uploaded_by_user(username, filename)
            if not file_info:
                header = {
                    'Feedback': 'Download',
                    'stat': 'FileNotExist',
                    'fileSize': '',
                    'user': username
                }
                self.send_header(connection, header, '128s')
                download_log = '\n%s try to download file "%s" at "%s" , Stat: FileNotExist ' % (username, filename, time)
            else:
                file_path = file_info['filepath']
                header = {
                    'Feedback': 'Download',
                    'stat': 'Success',
                    'fileSize': os.stat(file_path).st_size,
                    'user': username
                }
                self.send_header(connection, header, '128s')
                self.send_file(connection, file_path)
                download_log = '\n%s download a file "%s" at %s' % (username, filename, time)
        else:
            header = {
                'Feedback': 'Download',
                'stat': 'LoginFail',
                'fileSize': '',
                'user': username
            }
            self.send_header(connection, header, '128s')
            download_log = '\n%s try to download file "%s" at "%s" , Stat: LoginFail ' % (username, filename, time)
        self.write_log(download_log)

    def send_file_info_list(self, connection, header):
        username = header['user']
        # send the filenames which the user upload on the server to the client
        sql = "select filename, upload_time, size from fileinfo where username = '%s'" % (username)
        self.__cursor.execute(sql)
        data = self.__cursor.fetchall()
        self.send_header(connection, data, '1024s')

    def delete_file(self, connection, header):
        username = header['user']
        password = header['password']
        time = header['time']
        filename = header['fileName']
        delete_file_log = ''
        if self.check_user_password(username, password):
            file_info = self.get_file_info_uploaded_by_user(username, filename)
            if not file_info:
                header = {
                    'Feedback': 'DeleteFile',
                    'stat': 'FileNotExist',
                    'fileSize': '',
                    'user': username
                }
                self.send_header(connection, header, '128s')
                delete_file_log = '\n%s try to delete file "%s" at "%s" , Stat: FileNotExist ' % (username, filename, time)
            else:
                # delete the file
                os.remove(file_info['filepath'])
                # delete the record in table
                sql = "delete from fileinfo where username = '%s' and filename = '%s'" % (username, filename)
                self.__cursor.execute(sql)
                self.__db.commit()
                # send response
                header = {
                    'Feedback': 'DeleteFile',
                    'stat': 'Success',
                    'fileSize': '',
                    'user': username
                }
                self.send_header(connection, header, '128s')
                delete_file_log = '\n%s try to delete file "%s" at "%s" , Stat: Success ' % (username, filename, time)
        else:
            header = {
                'Feedback': 'DeleteFile',
                'stat': 'LoginFail',
                'fileSize': '',
                'user': username
            }
            self.send_header(connection, header, '128s')
            delete_file_log = '\n%s try to delete file "%s" at "%s" , Stat: LoginFail ' % (username, filename, time)
        self.write_log(delete_file_log)

    def do_command(self, connection, header):
        command = header['Command']
        if command == 'Login':
            self.login(connection, header)
        elif command == 'Logout':
            self.logout(connection, header)
        elif command == 'Register':
            self.register(connection, header)
        elif command == 'Upload':
            self.upload(connection, header)
        elif command == 'Download':
            self.download(connection, header)
        elif command == 'Update':
            self.send_file_info_list(connection, header)
        elif command == 'DeleteFile':
            self.delete_file(connection, header)
        elif command == 'DeleteUser':
            # @TODO: delete all the record and file about the user
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
                if header['Command'] == 'Logout':
                    break
            except socket.timeout:
                connection.close()
                break
            except ConnectionResetError:
                connection.close()
                break


if __name__ == "__main__":
    server = Server()
    server.server_listen()