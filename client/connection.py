import socket
import json
import math
from difflib import context_diff
from os import WCONTINUED


class Connection:
    def __init__(self, server, port):
        self.adress = (server, port)
        self.image_adress = (server, port+1)
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_main_socket(self):
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.connect(self.adress)
        print('------------')
        self.send('main')
    
    def connect_extra_socket(self, id):
        self.extra_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.extra_socket.connect(self.adress)
        self.send(id, self.extra_socket)
    
    def get_start(self):
        return self.recv()
    
    def get_game_state(self, options):
        self.send(options)
        game_state = self.recv()
        return game_state
    
    def recv(self, socket=None):
        if not socket:
            socket = self.main_socket
        data = {}
        try:
            response = socket.recv(2048)
            #print('recv bytes', response)
            str_data = response.decode()
            data = json.loads(str_data)
            #print(f'recv data: {data}')
        except Exception as err:
            #pass
            print('connection error : ', err)
        return data

    def recv_img(self, image_path: str):
        image_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        image_socket.connect(self.image_adress)

        self.send(image_path, image_socket)

        img_part_bytes = image_socket.recv(1024)
        img_full_bytes = b''

        while img_part_bytes:
            img_full_bytes += img_part_bytes
            img_part_bytes = image_socket.recv(1024)
            #print(f'RECIEVED BYTES: {img_part_bytes}')
        print(f'real image size: {len(img_full_bytes)}')
        return img_full_bytes

    def send(self, data, socket=None):
        print("Sending ", data)
        socket = socket or self.main_socket
        try:
            str_options = json.dumps(data)
            byte_options = str_options.encode()
            socket.send(byte_options)
#            response = self.main_socket.recv(1024)
        except Exception as err:
            #pass
            print('connection error : ', err)

    def kill(self):
        try:
            self.main_socket.close()
            self.extra_socket.close()
        except Exception as err:
            print(err)

    