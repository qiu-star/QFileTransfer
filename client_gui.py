from tkinter import *
from tkinter.messagebox import *
from tkinter import ttk
from tkinter import filedialog
from client import *
import pickle
import re, threading, time, operator

global stop_threads 
stop_threads = False
    
class FileListFrame(Frame):
    def __init__(self, master=None, client=None, file_info_list=None):
        Frame.__init__(self, master)
        self.root = master
        self.scrollbar = Scrollbar(self.root, )
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.client = client
        if file_info_list:
            self.file_info_list = file_info_list
        else:
            self.file_info_list = {}
        self.create_frame()
    
    def create_frame(self):
        title = ['2', '3', '4', ]
        self.box = ttk.Treeview(self, columns=title,
                                yscrollcommand=self.scrollbar.set,
                                show='headings', height=15)
        self.box.column('2', width=300, anchor='center')
        self.box.heading('2', text='文件名')
        self.box.column('3', width=150, anchor='center')
        self.box.heading('3', text='上传时间')
        self.box.column('4', width=150, anchor='center')
        self.box.heading('4', text='文件大小')

        for file_info in self.file_info_list:
            self.box.insert('', 'end', values=[value for key, value in file_info.items()])

        self.scrollbar.config(command=self.box.yview)
        self.box.pack()
        Label(self, text=" ", fg='red').pack()

        Button(self, text=' 下载 ', command=self.download).pack(expand=1, fill="both", side="left", anchor="w")
        Button(self, text=' 删除 ', command=self.delete_file).pack(expand=1, fill="both", side="left", anchor="w")
        Button(self, text=' 退出 ', command=self.quit_exe).pack(expand=1, fill="both", side="left", anchor="w")

    def quit_exe(self):
        global stop_threads 
        stop_threads = True
        self.client.logout(self.client.username, self.client.password)
        self.quit()

    def update_file_list(self):
        while True:
            global stop_threads 
            if stop_threads: 
                break
            file_info_list = self.client.get_file_info_list(self.client.username)
            if not operator.eq(self.file_info_list, file_info_list):  # not equal
                # delete old file info
                old_items = self.box.get_children()
                for item in old_items:
                    self.box.delete(item)
                # insert new file info
                for file_info in file_info_list:
                    self.box.insert('', 'end', values=[value for key, value in file_info.items()])
            time.sleep(5) # wait for a second

    def delete_file(self):
        file_item = self.box.focus()
        filename = self.box.item(file_item)['values'][0]
        self.client.delete_file(self.client.username, self.client.password, filename)
        showinfo(message='删除成功!')
        self.box.delete(file_item)

    def download(self):
        file_item = self.box.focus()
        filename = self.box.item(file_item)['values'][0]
        showinfo('提示！', message='点击确认文件将开始后台下载')
        thread = threading.Thread(target=self.client.download, args=(filename, self.client.username, self.client.password, ))
        thread.start()
    
class UploadFrame(Frame):
    def __init__(self, master=None, client=None):
        Frame.__init__(self, master)
        self.root = master
        self.file_path = StringVar()
        self.client = client
        self.create_frame()
    
    def create_frame(self):
        Label(self).grid(row=0, stick=W, pady=10)
        Label(self, text='请选择要上传的文件: ').grid(row=1, stick=W, pady=10)
        Entry(self, textvariable=self.file_path, width=50).grid(row=1, column=1, stick=E)
        Button(self, text=' 选择文件 ', command=self.select_file).grid(row=1, column=2, stick=E, padx=10)
        Button(self, text='上传', bg='#99CCFF', command=self.upload).grid(row=2, column=1, stick=W, pady=10, ipadx=50)
        Button(self, text='重置', bg='#FF6666',command=self.reset).grid(row=2, column=1, stick=E, pady=10, ipadx=50)

    def select_file(self):
        file_path = filedialog.askopenfilename()
        self.file_path.set(file_path)
    
    def upload(self):
        file_path = self.file_path.get()
        showinfo('提示！', message='点击确认文件将开始后台上传')
        thread = threading.Thread(target=self.client.upload, args=(file_path, self.client.username, ))
        thread.start()
        self.file_path.set("")
    
    def reset(self):
        self.file_path.set("")

class MeFrame(Frame):
    def __init__(self, master=None, client=None):
        Frame.__init__(self, master)
        self.root = master  # 定义内部变量root
        self.client = client
        self.create_frame()
    
    def create_frame(self):
        Label(self).grid(row=0, stick=W, pady=50)
        Label(self, text='Username: '+self.client.username).grid(row=1, stick=W, pady=3)
        Button(self, text=' 注销用户 ', command=self.delete_user).grid(row=1, column=2, stick=E, padx=10)

    def delete_user(self):
        global stop_threads
        stop_threads = True
        self.client.delete_user(self.client.username, self.client.password)
        self.quit()

class MainPage(object):
    def __init__(self, master=None, client=None, file_info_list=None):
        self.root = master  # 定义内部变量root
        self.root.geometry('%dx%d' % (780, 400))  # 设置窗口大小
        self.client = client
        self.file_info_list = file_info_list
        # create page
        self.create_page()
    
    def create_page(self):
        self.file_list_frame = FileListFrame(self.root, self.client, self.file_info_list)
        self.upload_frame = UploadFrame(self.root, self.client)
        self.me_frame = MeFrame(self.root, self.client)
        self.file_list_frame.pack()  # show file_list frame
        menubar = Menu(self.root)
        menubar.add_command(label='文件列表', command=self.show_file_list)
        menubar.add_command(label='上传文件', command=self.upload_file)
        menubar.add_command(label='个人信息', command=self.about_me)
        self.root['menu'] = menubar
        self.root.resizable(0, 0)

        thread = threading.Thread(target=self.file_list_frame.update_file_list,)
        thread.start()

    def show_file_list(self):
        self.file_list_frame.pack()
        self.upload_frame.pack_forget()
        self.me_frame.pack_forget()

    def upload_file(self):
        self.file_list_frame.pack_forget()
        self.upload_frame.pack()
        self.me_frame.pack_forget()
    
    def about_me(self):
        self.file_list_frame.pack_forget()
        self.upload_frame.pack_forget()
        self.me_frame.pack()

class LoginPage(object):
    def __init__(self, master=None):
        self.root = master
        self.root.geometry('%dx%d' % (450, 300))  # set up the window size
        self.root.title('文件安全传输系统')
        self.username = StringVar()
        self.password = StringVar()
        # create page
        self.create_page()

    def create_page(self):
        self.page = Frame(self.root)
        self.page.pack()
        canvas = Canvas(self.page, height=300, width=500)
        canvas.pack(side='top')

        Label(self.page, text='用户名:').place(x=120, y=100)
        Entry(self.page, textvariable=self.username).place(x=200, y=100)
        Label(self.page, text='密  码:').place(x=120, y=140)
        Entry(self.page, textvariable=self.password, show='*').place(x=200, y=140)
        Button(self.page, text='登录', command=self.try_login).place(x=140, y=180)
        Button(self.page, text='注册', command=self.register).place(x=210, y=180)

    def try_login(self):
        username = self.username.get()
        password = self.password.get()
        if username == '' or password == '':
            showerror(message='用户名或密码为空')
            return
        client = Client()
        file_info_list = client.login(username, password)
        if not file_info_list:
            showerror(message='用户名或密码错误')
            return
        client.username = username
        client.password = password
        self.page.destroy()
        # when file_info_list == "SuccessLogin", whcih means the user hasn/t uploaded anything
        if isinstance(file_info_list, str):
            MainPage(self.root, client)
        else:
            MainPage(self.root, client, file_info_list)

    def try_register(self):
        register_username = self.register_username.get()
        register_password = self.register_password.get()
        register_password_reinput = self.register_password_reinput.get()
        if register_username == '' or register_password == '':
            showerror(message='用户名或密码为空')
            return
        if register_password != register_password_reinput:
            showerror(message='输入密码不一致')
            return
        client = Client()
        stat = client.register(register_username, register_password)
        if stat:
            showinfo('欢迎', '注册成功')
            self.register_page.destroy()
        else:
            showerror(message='用户名已存在')


    def register(self):
        # set up the register page
        self.register_page = Toplevel(self.page)
        self.register_page.geometry('350x200')
        self.register_page.title('注册')

        self.register_username = StringVar()
        self.register_password = StringVar()
        self.register_password_reinput = StringVar()

        Label(self.register_page, text='用户名：').place(x=10, y=10)
        Entry(self.register_page, textvariable=self.register_username).place(x=150, y=10)
        Label(self.register_page, text='请输入密码：').place(x=10, y=50)
        Entry(self.register_page, textvariable=self.register_password, show='*').place(x=150, y=50)
        Label(self.register_page, text='请再次输入密码：').place(x=10, y=90)
        Entry(self.register_page, textvariable=self.register_password_reinput, show='*').place(x=150, y=90)

        button = Button(self.register_page, text='确认注册', command=self.try_register)
        button.place(x=150, y=130)