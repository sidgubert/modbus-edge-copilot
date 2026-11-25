import logging
import time
from pymodbus.client import ModbusTcpClient
from cache import DiagnosticCache
from diagnostics import run_local_inference

logging.basicConfig(level=logging.INFO, format="%(asctime)s [EDGE-GW] %(message)s")


def parse_registers(registers: list[int]) -> dict:
    # Converte valores inteiros Modbus (signed para temperatura)
    raw_temp = registers[0] if registers[0] < 32768 else registers[0] - 65536
    return {
        "temperatura_camara_c": round(raw_temp / 10.0, 1),
        "pressao_succao_psi": round(registers[1] / 10.0, 1),
        "pressao_descarga_psi": round(registers[2] / 10.0, 1),
        "corrente_compressor_a": round(registers[3] / 10.0, 1),
        "codigo_alarme": registers[4],
    }


def main():
    client = ModbusTcpClient("127.0.0.1", port=5020)
    cache = DiagnosticCache()

    if not client.connect():
        logging.error("Falha ao conectar no CLP Modbus TCP (127.0.0.1:5020).")
        return

    logging.info("Gateway conectado ao CLP. Iniciando monitoramento determinístico...")

    try:
        while True:
            result = client.read_holding_registers(address=0, count=5)
            if result.isError():
                logging.warning("Erro na leitura dos registradores Modbus.")
                time.sleep(2)
                continue

            telemetry = parse_registers(result.registers)

            # 1. Camada Determinística: IA só é acionada se houver alarme ou desvio físico
            if telemetry["codigo_alarme"] == 0:
                logging.info(f"Operação nominal: {telemetry}")
                time.sleep(2)
                continue

            # 2. Camada de Cache de Estado (latência < 5ms)
            t0 = time.perf_counter()
            cached = cache.get(
                telemetry["codigo_alarme"],
                telemetry["temperatura_camara_c"],
                telemetry["pressao_descarga_psi"],
            )

            if cached:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                logging.info(f"[CACHE HIT - {elapsed_ms:.2f}ms] Diagnóstico: {cached}")
            else:
                logging.warning(f"Anomalia detectada! Acionando inferência local: {telemetry}")
                diagnosis = run_local_inference(telemetry)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                cache.set(
                    telemetry["codigo_alarme"],
                    telemetry["temperatura_camara_c"],
                    telemetry["pressao_descarga_psi"],
                    diagnosis,
                )
                logging.info(f"[LLM LOCAL - {elapsed_ms:.0f}ms] Diagnóstico: {diagnosis}")

            time.sleep(2)
    finally:
        client.close()


if __name__ == "__main__":
    main()
