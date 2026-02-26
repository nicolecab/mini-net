"""
transporte.py - Camada de Transporte (Fase 2) + Rede (Fase 3) + Enlace (Fase 4)
Implementa Stop-and-Wait com ACKs, Timeouts e Números de Sequência.
Encapsula em: Segmento → Pacote → Quadro (com CRC32).
"""

import socket
import json
import time
from protocol import enviar_pela_rede_ruidosa, Segmento, Pacote, Quadro

TIMEOUT = 0.5  # segundos para retransmissão

class Transporte:

    def __init__(self, sock, vip_local="HOST_A", mac_local="MAC_HOST_A"):
        self.sock       = sock
        self.seq        = 0           # número de sequência atual (0 ou 1)
        self.expected_seq = 0         # próximo seq esperado pelo receptor
        self.vip_local  = vip_local   # endereço virtual (Camada 3)
        self.mac_local  = mac_local   # endereço MAC fictício (Camada 4)

    # ================================================================
    # ENVIAR: Aplicação → Transporte → Rede → Enlace → Físico
    # ================================================================
    def enviar(self, mensagem, destino, dst_vip="SERVIDOR", dst_mac="MAC_SERVIDOR"):
        """
        mensagem : dicionário da aplicação (JSON)
        destino  : (IP, Porta) real do próximo salto (roteador ou servidor)
        dst_vip  : endereço virtual de destino
        dst_mac  : endereço MAC do próximo salto
        """

        while True:
            print(f"\033[33m[TRANSPORTE] Enviando segmento seq={self.seq}\033[0m")

            # ── Camada 4: Segmento ───────────────────────────────────
            segmento = Segmento(
                seq_num=self.seq,
                is_ack=False,
                payload=mensagem
            )

            # ── Camada 3: Pacote ─────────────────────────────────────
            pacote = Pacote(
                src_vip=self.vip_local,
                dst_vip=dst_vip,
                ttl=16,
                segmento_dict=segmento.to_dict()
            )

            # ── Camada 2: Quadro com CRC ─────────────────────────────
            quadro = Quadro(
                src_mac=self.mac_local,
                dst_mac=dst_mac,
                pacote_dict=pacote.to_dict()
            )
            bytes_quadro = quadro.serializar()

            # ── Camada 1: Canal ruidoso ──────────────────────────────
            enviar_pela_rede_ruidosa(self.sock, bytes_quadro, destino)
            self.sock.settimeout(TIMEOUT)

            try:
                data, _ = self.sock.recvfrom(65535)
                resposta_valida = self._desencapsular(data)

                if resposta_valida is None:
                    print("\033[91m[TRANSPORTE] ACK corrompido ou inválido. Retransmitindo...\033[0m")
                    continue

                seg_ack = resposta_valida
                if seg_ack["is_ack"] and seg_ack["seq_num"] == self.seq:
                    print(f"\033[32m[TRANSPORTE] ✓ ACK {self.seq} recebido!\033[0m")
                    self.sock.settimeout(None)
                    self.seq = 1 - self.seq
                    break
                else:
                    print("\033[33m[TRANSPORTE] ACK duplicado ou inesperado. Ignorando.\033[0m")

            except socket.timeout:
                print("\033[33m[TRANSPORTE] ✗ Timeout! Retransmitindo...\033[0m")

    # ================================================================
    # RECEBER: Físico → Enlace → Rede → Transporte → Aplicação
    # ================================================================
    def receber(self):
        """
        Retorna: (payload_da_aplicação, addr_origem) ou (None, None)
        """
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
            except Exception as e:
                print(f"\033[91m[TRANSPORTE] Erro ao receber: {e}\033[0m")
                return None, None

            # ── Camada 2: Verificar CRC ──────────────────────────────
            quadro_dict, integro = Quadro.deserializar(data)

            if not integro or quadro_dict is None:
                print("\033[91m[ENLACE] ✗ Erro de CRC! Quadro descartado silenciosamente.\033[0m")
                # A camada de transporte vai recuperar via timeout do remetente
                continue

            print(f"\033[92m[ENLACE] ✓ CRC válido. src_mac={quadro_dict['src_mac']}\033[0m")

            # ── Camada 3: Rede ───────────────────────────────────────
            pacote_dict = quadro_dict["data"]
            print(f"\033[94m[REDE] Pacote: src={pacote_dict['src_vip']} dst={pacote_dict['dst_vip']} TTL={pacote_dict['ttl']}\033[0m")

            # ── Camada 4: Segmento ───────────────────────────────────
            seg = pacote_dict["data"]
            seq = seg["seq_num"]

            if not seg["is_ack"]:
                # É dado: verificar sequência
                if seq == self.expected_seq:
                    print(f"\033[32m[TRANSPORTE] ✓ Segmento correto seq={seq}\033[0m")

                    # Enviar ACK
                    self._enviar_ack(seq, addr)
                    self.expected_seq = 1 - self.expected_seq
                    return seg["payload"], addr

                else:
                    print(f"\033[33m[TRANSPORTE] Duplicata detectada (seq={seq}, esperado={self.expected_seq}). Reenviando ACK anterior.\033[0m")
                    self._enviar_ack(1 - self.expected_seq, addr)
                    # continua o loop para tentar receber o pacote correto
            else:
                # É um ACK chegando na função receber (não esperado aqui normalmente)
                return seg, addr

    # ================================================================
    # AUXILIARES PRIVADOS
    # ================================================================
    def _enviar_ack(self, seq_num, destino):
        """Monta e envia um ACK encapsulado em Quadro/Pacote."""
        seg_ack = Segmento(seq_num=seq_num, is_ack=True, payload=None)
        pacote  = Pacote(src_vip=self.vip_local, dst_vip="ORIGEM", ttl=16, segmento_dict=seg_ack.to_dict())
        quadro  = Quadro(src_mac=self.mac_local, dst_mac="MAC_ORIGEM", pacote_dict=pacote.to_dict())
        bytes_ack = quadro.serializar()
        # ACK usa envio direto (sem ruído) para simplificar; o ruído já é simulado no canal de dados
        # Se quiser máxima fidelidade, substitua por enviar_pela_rede_ruidosa:
        self.sock.sendto(bytes_ack, destino)
        print(f"\033[32m[TRANSPORTE] ACK {seq_num} enviado para {destino}\033[0m")

    def _desencapsular(self, data):
        """Desencapsula Quadro → Pacote → Segmento. Retorna dict do segmento ou None."""
        quadro_dict, integro = Quadro.deserializar(data)
        if not integro or quadro_dict is None:
            print("\033[91m[ENLACE] ✗ CRC inválido no ACK recebido.\033[0m")
            return None
        pacote_dict = quadro_dict.get("data", {})
        seg = pacote_dict.get("data", None)
        return seg
