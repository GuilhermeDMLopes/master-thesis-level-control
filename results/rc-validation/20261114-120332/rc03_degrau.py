import asyncio
import csv
import json
import math
import sys
import time
from pathlib import Path
from asyncua import Client, ua

URL = "opc.tcp://10.0.0.2:4840"
OUT = Path(sys.argv[1])
report = {
    "teste": "RC-03",
    "resultado": "INCOMPLETO",
    "endpoint": URL,
    "retorno_confirmado": False,
    "leituras": 0,
    "escritas_solicitadas": [],
}

async def main():
    async with Client(URL, timeout=5) as client:
        namespaces = await client.get_namespace_array()
        ns = namespaces.index("urn:B&R/pv/")
        nodes = [
            client.get_node(ua.NodeId("::Program:" + name, ns))
            for name in ("ACAO_CONTROLE", "ADC_R")
        ]

        for node in nodes:
            dtype = await node.read_data_type_as_variant_type()
            if dtype != ua.VariantType.Float:
                raise RuntimeError("Tipo inesperado: exige REAL/Float.")

        async def read():
            values = await client.read_values(nodes)
            if not all(
                isinstance(v, (int, float)) and math.isfinite(v)
                for v in values
            ):
                raise RuntimeError("Leitura invalida: " + repr(values))
            return values

        initial, pv = await read()
        report["comando_inicial"] = initial
        report["adc_inicial"] = pv

        if min(abs(initial), abs(initial - 1.0)) > 1e-5:
            raise RuntimeError(
                f"ACAO_CONTROLE={initial}; esperado 0.0 ou 1.0. "
                "Nenhuma escrita realizada."
            )

        start = time.monotonic()

        async def write(value):
            report["escritas_solicitadas"].append({
                "valor": value,
                "tempo_pc_s": time.monotonic() - start,
            })
            await nodes[0].write_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(ua.Variant(value, ua.VariantType.Float))
            )

        print("PLC RC conectado:", URL, flush=True)
        print("Sequencia: preparar 1.0 por 8 s -> 2.0 por 8 s -> 1.0 por 8 s.")
        print("Fase        Tempo(s)    Comando       ADC_R", flush=True)

        with (OUT / "amostras.csv").open(
            "x", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow([
                "fase", "tempo_pc_s", "tempo_fase_s",
                "acao_controle_lida", "adc_r",
            ])

            async def record(phase, duration, expected):
                begin = time.monotonic()
                deadline = begin + duration
                next_print = 0.0

                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break

                    u, y = await asyncio.wait_for(
                        read(), timeout=remaining
                    )
                    now = time.monotonic()
                    elapsed = now - begin

                    writer.writerow([
                        phase, now - start, elapsed, u, y
                    ])
                    file.flush()
                    report["leituras"] += 1

                    if abs(u - expected) > 1e-5:
                        raise RuntimeError(
                            f"Comando divergente em {phase}: "
                            f"esperado {expected}, lido {u}"
                        )

                    if elapsed >= next_print:
                        print(
                            f"{phase:10s} {now-start:8.3f} "
                            f"{u:10.5f} {y:11.5f}",
                            flush=True,
                        )
                        next_print = elapsed + 0.5

                    await asyncio.sleep(
                        min(0.1, max(0.0, deadline - time.monotonic()))
                    )

            # Preparacao realizada dentro do try/finally abaixo.

            try:
                print("Preparando ACAO_CONTROLE = 1.0 por 8 segundos.", flush=True)
                await write(1.0)
                await record("preparo", 8.0, 1.0)
                print("Aplicando ACAO_CONTROLE = 2.0", flush=True)
                await write(2.0)
                await record("degrau", 8.0, 2.0)
            finally:
                # Tenta restaurar mesmo se a escrita ou leitura falhar.
                try:
                    print("Restaurando ACAO_CONTROLE = 1.0", flush=True)
                    await write(1.0)
                    restored, _ = await read()

                    if abs(restored - 1.0) > 1e-5:
                        raise RuntimeError(
                            f"Retorno divergente: {restored}"
                        )

                    report["retorno_confirmado"] = True
                    print("Retorno a 1.0 confirmado por leitura.",
                          flush=True)
                except BaseException as exc:
                    report["erro_retorno"] = repr(exc)
                    print(
                        "RETORNO NAO CONFIRMADO. Restaure "
                        "ACAO_CONTROLE = 1.0 no Automation Studio.",
                        flush=True,
                    )
                    raise

            await record("retorno", 8.0, 1.0)
            report["resultado"] = "COLETA_CONCLUIDA"

try:
    asyncio.run(main())
except BaseException as exc:
    report["erro"] = repr(exc)
    raise
finally:
    (OUT / "resumo.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("Resultado:", report["resultado"])
    print("Evidencias:", OUT)