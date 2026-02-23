import socket
import json
import time
from transporte import Transporte

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
transporte = Transporte(sock)
username = input("Digite seu nome de usuário: ")

while True:
    text = input("Mensagem: ")

    message = {
        "type": "chat",
        "sender": username,
        "message": text,
        "timestamp": time.time()
    }

    transporte.enviar(message, (SERVER_IP, SERVER_PORT))

    payload, _ = transporte.receber()
    
    if payload:
        print(f"[APLICAÇÃO] Resposta: {payload['message']}")