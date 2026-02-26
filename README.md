# Mini-NET — Projeto Integrador de Redes

Chat funcional implementado sobre UDP com pilha de protocolos completa (Aplicação → Transporte → Rede → Enlace), simulando perda e corrupção de pacotes.

## Arquitetura

```
[client.py]  →  [router.py]  →  [server.py]
   HOST_A          ROTEADOR        SERVIDOR
   :7000            :6000           :5000

Encapsulamento:  JSON (Aplicação)
              →  Segmento (Transporte) — Stop-and-Wait, ACK, Timeout, Seq 0/1
              →  Pacote (Rede)         — VIP src/dst, TTL
              →  Quadro (Enlace)       — MAC src/dst, CRC32
              →  Canal ruidoso (Física) — Perda 20%, Corrupção 20%
```

## Como rodar

Abra **3 terminais** na pasta do projeto:

### Terminal 1 — Servidor
```bash
python server.py
```

### Terminal 2 — Roteador
```bash
python router.py
```

### Terminal 3 — Cliente
```bash
python client.py
```

> Digite seu nome de usuário quando solicitado e comece a enviar mensagens.

## Cores nos logs

| Cor | Camada/Evento |
|-----|--------------|
| 🔴 Vermelho | Erro de CRC / pacote perdido / TTL expirado |
| 🟡 Amarelo  | Retransmissão de transporte / timeout |
| 🟢 Verde    | Mensagem entregue / ACK confirmado / CRC válido |
| 🔵 Azul     | Camada de Rede (roteador) |
| 🩵 Ciano    | Prompt do cliente |

## Arquivos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `protocol.py` | Estruturas PDU (Segmento, Pacote, Quadro) + simulador físico |
| `transporte.py` | Stop-and-Wait, ACK, Timeout, encapsulamento completo |
| `router.py` | Tabela de roteamento estática, decremento TTL |
| `server.py` | Aplicação servidora |
| `client.py` | Aplicação cliente |

## Configurações de simulação (protocol.py)

```python
PROBABILIDADE_PERDA    = 0.2   # 20% de pacotes perdidos
PROBABILIDADE_CORRUPCAO = 0.2  # 20% de pacotes corrompidos
LATENCIA_MIN = 0.1             # atraso mínimo (s)
LATENCIA_MAX = 0.5             # atraso máximo (s)
```

Para testar o pior caso, altere para `0.5` e observe o Stop-and-Wait retransmitindo automaticamente.
