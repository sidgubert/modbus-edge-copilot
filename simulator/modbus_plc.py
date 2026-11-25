import asyncio
import logging
import random
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CLP-SIM] %(message)s")

# Mapa de Registradores (Holding Registers - HR)
# HR 0: Temperatura Câmara (°C * 10) -> Ex: -185 = -18.5°C
# HR 1: Pressão Sucção (PSI * 10)   -> Ex: 240 = 24.0 PSI
# HR 2: Pressão Descarga (PSI * 10) -> Ex: 2150 = 215.0 PSI
# HR 3: Corrente Compressor (A * 10)-> Ex: 142 = 14.2 A
# HR 4: Código de Alarme (0=OK, 101=Alta Pressão Descarga, 102=Sobrecorrente, 103=Deriva Térmica)


async def simulate_process(server: ModbusTcpServer):
    tick = 0
    device_id = 0x00
    while True:
        await asyncio.sleep(2)
        tick += 1

        # Operação normal nos primeiros 10 segundos, depois injeta anomalia gradual
        if tick < 5:
            temp = random.randint(-190, -180)      # -19.0°C a -18.0°C
            p_suc = random.randint(230, 250)       # 23.0 a 25.0 PSI
            p_desc = random.randint(2100, 2200)    # 210 a 220 PSI
            amp = random.randint(138, 145)         # 13.8 a 14.5 A
            alarm = 0
        else:
            # Simula condensador sujo / falha de ventilação na condensadora
            temp = random.randint(-145, -130)      # Subindo: -14.5°C
            p_suc = random.randint(280, 310)       # Subindo: 29.0 PSI
            p_desc = random.randint(2850, 3050)    # Crítico: ~295.0 PSI
            amp = random.randint(185, 198)         # Alta corrente: ~19.2 A
            alarm = 101                            # Alarme: Alta Pressão de Descarga

        # Converte temperatura negativa para inteiro 16-bit unsigned (complemento de dois)
        await server.async_setValues(
            device_id, 3, 0, [temp & 0xFFFF, p_suc, p_desc, amp, alarm]
        )
        logging.info(
            f"Telemetria atualizada | Temp: {temp/10:.1f}°C | P.Desc: {p_desc/10:.1f} PSI | "
            f"Corrente: {amp/10:.1f}A | Alarme: {alarm}"
        )


async def run_server():
    device = SimDevice(
        id=0,
        simdata=[SimData(0, values=[0] * 10, datatype=DataType.REGISTERS)],
    )
    server = ModbusTcpServer(context=device, address=("127.0.0.1", 5020))

    logging.info("Iniciando Simulador Modbus TCP na porta 5020...")
    sim_task = asyncio.create_task(simulate_process(server))
    try:
        await server.serve_forever()
    finally:
        sim_task.cancel()


if __name__ == "__main__":
    asyncio.run(run_server())
