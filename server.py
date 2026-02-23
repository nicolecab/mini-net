import socket
import json
from transporte import Transporte

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))
transporte = Transporte(sock)

print("Servidor iniciando...")

while True:
    payload, addr = transporte.receber()

    if payload:
        print(f"[APLICAÇÃO] Mensagem recebida de {payload['sender']}: {payload['message']}")

        resposta = {
            "type": "chat",
            "sender": "Servidor",
            "message": "Recebido!",
            "timestamp": payload["timestamp"]
        }

        transporte.enviar(resposta, addr)