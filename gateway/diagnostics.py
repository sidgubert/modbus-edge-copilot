import json
import requests
from pydantic import BaseModel, Field

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "qwen2.5:7b"  # Pode trocar por llama3.2:3b ou mistral conforme VRAM


class DiagnosticReport(BaseModel):
    causa_provavel: str = Field(description="Causa raiz física mais provável da anomalia")
    acao_imediata: str = Field(description="Verificação física objetiva para o técnico de campo")
    criticidade: str = Field(description="BAIXA, MEDIA ou CRITICA")
    risco_parada: bool = Field(description="True se houver risco iminente de dano ao compressor")


def run_local_inference(telemetry: dict) -> dict:
    prompt = (
        "Você é um engenheiro especialista em refrigeração industrial e manutenção. "
        "Analise a telemetria lida via Modbus TCP de uma câmara fria com compressor semi-hermético "
        "e retorne estritamente o diagnóstico técnico estruturado.\n\n"
        f"Telemetria atual: {json.dumps(telemetry, ensure_ascii=False)}"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": DiagnosticReport.model_json_schema(),
        "options": {"temperature": 0.1},
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=30)
    response.raise_for_status()
    raw_content = response.json()["message"]["content"]

    # Validação determinística do contrato de saída
    validated = DiagnosticReport.model_validate_json(raw_content)
    return validated.model_dump()
