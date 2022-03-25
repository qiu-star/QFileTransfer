from tkinter import *
from tkinter.messagebox import *
from client import *
import pickle
import threading

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
        print(not file_info_list)
        if not file_info_list:
            showerror(message='用户名或密码错误')
            return
        print(file_info_list)  # @TODO: when file_info_list == "SuccessLogin", whcih means the user hasn/t uploaded anything
        self.page.destroy()
        # @TODO: show list 

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