# modbus-edge-copilot

Gateway de diagnóstico industrial *local-first* para sistemas de refrigeração e utilidades. Lê registradores via **Modbus TCP**, aplica detecção determinística de anomalias e utiliza **LLMs locais (Ollama)** com **cache de estado** e **saída estruturada estrita (Pydantic)** — sem enviar telemetria operacional para a nuvem.

## Princípios de Arquitetura
1. **IA não substitui intertravamento:** A detecção de falha ocorre por regras físicas determinísticas nos registradores Modbus. O LLM atua exclusivamente no diagnóstico assistido.
2. **Privacidade e Latência Zero-Cloud:** Todo o processamento roda na borda (*on-premise*).
3. **Cache de Estado Operacional:** Falhas recorrentes são respondidas em `< 5 ms` sem reprocessamento de tokens.
4. **Contrato de Saída Estrito:** Respostas validadas via JSON Schema (`Pydantic`), eliminando texto livre não estruturado.

## Como Executar
1. Instale o [Ollama](https://ollama.com/) e baixe o modelo:
   ```bash
   ollama pull qwen2.5:7b
   ```
2. Instale as dependências Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie o simulador de CLP Modbus TCP:
   ```bash
   python simulator/modbus_plc.py
   ```
4. Em outro terminal, inicie o Edge Gateway:
   ```bash
   python gateway/main.py
   ```
