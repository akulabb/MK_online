import socket

SERVER = 'localhost'
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((SERVER, PORT))

try:
	response = server.recv(1024)
	print('полученны координаты : ', response)
except Exception as err:
	print('connection error : ', err)