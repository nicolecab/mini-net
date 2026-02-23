import socket
import json
import time
from protocol import enviar_pela_rede_ruidosa, Segmento

TIMEOUT = 2

class Transporte:
    
    def __init__(self, sock):
        self.sock = sock
        self.seq = 0
        self.expected_seq = 0

    def enviar(self, mensagem, destino):
        segmento = {
            "type": "data",
            "seq": self.seq,
            "payload": mensagem
        }

        while True:
            print(f"[TRANSPORTE] Enviando segmento seq={self.seq}")

            bytes_segmento = json.dumps(segmento).encode()
            enviar_pela_rede_ruidosa(self.sock, bytes_segmento, destino)
            self.sock.settimeout(TIMEOUT)

            try:
                data, _ = self.sock.recvfrom(4096)
                resposta = json.loads(data.decode())

                if resposta["type"] == "ack" and resposta["ack"] == self.seq:
                    print(f"[TRANSPORTE] ACK {self.seq} recebido")
                    self.sock.settimeout(None)
                    self.seq = 1 - self.seq
                    break

            except socket.timeout:
                print("[TRANSPORTE] Timeout! Retransmitindo...")

    def receber(self):
        data, addr = self.sock.recvfrom(4096)
        segmento = json.loads(data.decode())

        if segmento["type"] == "data":
            seq = segmento["seq"]

            if seq == self.expected_seq:
                print(f"[TRANSPORTE] Segmento correto seq={seq}")

                ack = {
                    "type": "ack",
                    "ack": seq
                }

                bytes_ack = json.dumps(ack).encode()
                enviar_pela_rede_ruidosa(self.sock, bytes_ack, addr)
                self.expected_seq = 1 - self.expected_seq

                return segmento["payload"], addr

            else:
                print("[TRANSPORTE] Duplicata detectada")

                ack = {
                    "type": "ack",
                    "ack": 1 - self.expected_seq
                }

                self.sock.sendto(json.dumps(ack).encode(), addr)

        return None, None