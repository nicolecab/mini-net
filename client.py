"""
client.py - Cliente do Mini-Chat
Envia mensagens ao ROTEADOR (não diretamente ao servidor).
"""

import socket
import json
import time
from transporte import Transporte

# O cliente envia para o ROTEADOR, não para o servidor diretamente
ROUTER_IP   = "127.0.0.1"
ROUTER_PORT = 6000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

username = input("Digite seu nome de usuário: ")

# VIP e MAC do cliente
transporte = Transporte(sock, vip_local=username, mac_local=f"MAC_{username.upper()}")

print("\033[92m╔══════════════════════════════════╗\033[0m")
print("\033[92m║      Mini-NET Chat Cliente       ║\033[0m")
print(f"\033[92m║   Conectado como: {username:<14}║\033[0m")
print("\033[92m╚══════════════════════════════════╝\033[0m\n")

while True:
    try:
        text = input("\033[96mMensagem: \033[0m")
        if not text.strip():
            continue

        message = {
            "type": "chat",
            "sender": username,
            "message": text,
            "timestamp": time.time()
        }

        # Envia ao roteador com destino virtual = SERVIDOR
        transporte.enviar(
            message,
            destino=(ROUTER_IP, ROUTER_PORT),
            dst_vip="SERVIDOR",
            dst_mac="MAC_ROUTER"
        )

        # Aguarda resposta do servidor (que também virá pelo roteador)
        payload, _ = transporte.receber()

        if payload and isinstance(payload, dict):
            horario = time.strftime("%H:%M:%S", time.localtime(payload.get("timestamp", time.time())))
            print(f"\033[92m[APLICAÇÃO] [{horario}] {payload.get('sender','?')}: {payload.get('message','')}\033[0m\n")

    except KeyboardInterrupt:
        print("\n\033[93m[CLIENTE] Encerrando...\033[0m")
        break
