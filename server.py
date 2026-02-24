"""
server.py - Servidor do Mini-Chat
Escuta mensagens do roteador, exibe e responde ao remetente.
"""

import socket
import json
import time
from transporte import Transporte

SERVER_IP   = "127.0.0.1"
SERVER_PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

# VIP do servidor e MAC fictício
transporte = Transporte(sock, vip_local="SERVIDOR", mac_local="MAC_SERVIDOR")

print("\033[92m╔══════════════════════════════════╗\033[0m")
print("\033[92m║   Mini-NET Servidor iniciado!    ║\033[0m")
print(f"\033[92m║   Escutando em {SERVER_IP}:{SERVER_PORT}   ║\033[0m")
print("\033[92m╚══════════════════════════════════╝\033[0m\n")

while True:
    payload, addr = transporte.receber()

    if payload:
        sender    = payload.get("sender", "Desconhecido")
        mensagem  = payload.get("message", "")
        timestamp = payload.get("timestamp", time.time())

        horario = time.strftime("%H:%M:%S", time.localtime(timestamp))
        print(f"\033[92m[APLICAÇÃO] [{horario}] {sender}: {mensagem}\033[0m")

        resposta = {
            "type": "chat",
            "sender": "Servidor",
            "message": f"Recebido: '{mensagem}'",
            "timestamp": time.time()
        }

        # Responde de volta ao roteador (que encaminhará ao cliente)
        # addr aqui é o roteador (último salto)
        transporte.enviar(
            resposta,
            destino=addr,
            dst_vip=payload.get("sender", "HOST_A"),
            dst_mac="MAC_ROUTER"
        )
