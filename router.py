"""
router.py - Roteador Virtual (Fase 3)
Responsável por: Encaminhar pacotes com base no endereço virtual de destino (VIP).
Camada de Rede: lê dst_vip, consulta tabela e redireciona.
"""

import socket
import json
from protocol import Quadro, Pacote, Segmento, enviar_pela_rede_ruidosa

# ===================== CONFIGURAÇÃO DO ROTEADOR =====================
ROUTER_IP   = "127.0.0.1"
ROUTER_PORT = 6000

# Tabela de roteamento estática:  VIP  ->  (IP real, Porta real)
TABELA_ROTEAMENTO = {
    "SERVIDOR": ("127.0.0.1", 5000),
    "HOST_A":   ("127.0.0.1", 7000),   # reservado para futuros clientes
}

# ====================================================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ROUTER_IP, ROUTER_PORT))

print(f"\033[94m[ROTEADOR] Escutando em {ROUTER_IP}:{ROUTER_PORT}\033[0m")
print(f"\033[94m[ROTEADOR] Tabela de roteamento: {TABELA_ROTEAMENTO}\033[0m\n")

while True:
    try:
        dados_crus, addr_origem = sock.recvfrom(65535)
        print(f"\033[94m[ROTEADOR] Quadro recebido de {addr_origem}\033[0m")

        # ── Camada 2: Deserializar e verificar CRC ──────────────────
        quadro_dict, integro = Quadro.deserializar(dados_crus)

        if not integro or quadro_dict is None:
            print("\033[91m[ROTEADOR][ENLACE] ✗ Quadro corrompido (CRC inválido). Descartando.\033[0m")
            continue

        print(f"\033[92m[ROTEADOR][ENLACE] ✓ CRC válido. src_mac={quadro_dict['src_mac']} dst_mac={quadro_dict['dst_mac']}\033[0m")

        # ── Camada 3: Extrair Pacote ─────────────────────────────────
        pacote_dict = quadro_dict["data"]
        src_vip = pacote_dict["src_vip"]
        dst_vip = pacote_dict["dst_vip"]
        ttl     = pacote_dict["ttl"]

        print(f"\033[94m[ROTEADOR][REDE] Pacote: src_vip={src_vip} dst_vip={dst_vip} TTL={ttl}\033[0m")

        # Verificar TTL
        if ttl <= 0:
            print("\033[91m[ROTEADOR][REDE] ✗ TTL expirado! Pacote descartado.\033[0m")
            continue

        # Decrementar TTL
        pacote_dict["ttl"] = ttl - 1
        print(f"\033[94m[ROTEADOR][REDE] TTL decrementado para {pacote_dict['ttl']}\033[0m")

        # Consultar tabela de roteamento
        if dst_vip not in TABELA_ROTEAMENTO:
            print(f"\033[91m[ROTEADOR][REDE] ✗ Destino '{dst_vip}' não encontrado na tabela. Descartando.\033[0m")
            continue

        destino_real = TABELA_ROTEAMENTO[dst_vip]
        print(f"\033[94m[ROTEADOR][REDE] → Encaminhando para {destino_real}\033[0m")

        # ── Camada 2: Re-encapsular em novo Quadro ───────────────────
        novo_quadro = Quadro(
            src_mac="MAC_ROUTER",
            dst_mac=f"MAC_{dst_vip}",
            pacote_dict=pacote_dict
        )
        bytes_quadro = novo_quadro.serializar()

        # ── Camada 1: Enviar pelo canal ruidoso ──────────────────────
        enviar_pela_rede_ruidosa(sock, bytes_quadro, destino_real)
        print(f"\033[92m[ROTEADOR] ✓ Pacote encaminhado para {destino_real}\033[0m\n")

    except Exception as e:
        print(f"\033[91m[ROTEADOR] Erro inesperado: {e}\033[0m")
