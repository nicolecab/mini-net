"""
router.py - Roteador Virtual (Fase 3)
Possui tabela ARP dinâmica: aprende o endereço real dos clientes ao receber pacotes.
"""

import socket
import json
from protocol import Quadro, Pacote, Segmento, enviar_pela_rede_ruidosa

ROUTER_IP   = "127.0.0.1"
ROUTER_PORT = 6000

# Tabela estática: só o servidor precisa estar aqui
TABELA_ROTEAMENTO = {
    "SERVIDOR": ("127.0.0.1", 5000),
}

# Tabela ARP dinâmica: aprende clientes em tempo real
tabela_arp = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ROUTER_IP, ROUTER_PORT))

print(f"\033[94m[ROTEADOR] Escutando em {ROUTER_IP}:{ROUTER_PORT}\033[0m")
print(f"\033[94m[ROTEADOR] Tabela estática: {TABELA_ROTEAMENTO}\033[0m\n")

while True:
    try:
        dados_crus, addr_origem = sock.recvfrom(65535)
        print(f"\033[94m[ROTEADOR] Quadro recebido de {addr_origem}\033[0m")

        quadro_dict, integro = Quadro.deserializar(dados_crus)

        if not integro or quadro_dict is None:
            print("\033[91m[ROTEADOR][ENLACE] ✗ Quadro corrompido (CRC inválido). Descartando.\033[0m")
            continue

        print(f"\033[92m[ROTEADOR][ENLACE] ✓ CRC válido. src_mac={quadro_dict['src_mac']} dst_mac={quadro_dict['dst_mac']}\033[0m")

        pacote_dict = quadro_dict["data"]
        src_vip = pacote_dict["src_vip"]
        dst_vip = pacote_dict["dst_vip"]
        ttl     = pacote_dict["ttl"]

        print(f"\033[94m[ROTEADOR][REDE] Pacote: src_vip={src_vip} dst_vip={dst_vip} TTL={ttl}\033[0m")

        # Aprende endereço real do remetente (ARP dinâmico)
        if src_vip not in TABELA_ROTEAMENTO:
            tabela_arp[src_vip] = addr_origem
            print(f"\033[94m[ROTEADOR][ARP] Aprendi: {src_vip} → {addr_origem}\033[0m")

        if ttl <= 0:
            print("\033[91m[ROTEADOR][REDE] ✗ TTL expirado! Pacote descartado.\033[0m")
            continue

        pacote_dict["ttl"] = ttl - 1
        print(f"\033[94m[ROTEADOR][REDE] TTL decrementado para {pacote_dict['ttl']}\033[0m")

        # Roteamento: tabela estática primeiro, depois ARP dinâmica
        if dst_vip in TABELA_ROTEAMENTO:
            destino_real = TABELA_ROTEAMENTO[dst_vip]
        elif dst_vip in tabela_arp:
            destino_real = tabela_arp[dst_vip]
            print(f"\033[94m[ROTEADOR][ARP] Rota dinâmica: {dst_vip} → {destino_real}\033[0m")
        else:
            print(f"\033[91m[ROTEADOR][REDE] ✗ Destino '{dst_vip}' não encontrado. Descartando.\033[0m")
            continue

        print(f"\033[94m[ROTEADOR][REDE] → Encaminhando para {destino_real}\033[0m")

        novo_quadro = Quadro(
            src_mac="MAC_ROUTER",
            dst_mac=f"MAC_{dst_vip}",
            pacote_dict=pacote_dict
        )
        bytes_quadro = novo_quadro.serializar()

        enviar_pela_rede_ruidosa(sock, bytes_quadro, destino_real)
        print(f"\033[92m[ROTEADOR] ✓ Pacote encaminhado para {destino_real}\033[0m\n")

    except Exception as e:
        print(f"\033[91m[ROTEADOR] Erro inesperado: {e}\033[0m")
