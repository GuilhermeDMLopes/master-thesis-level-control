"""RC-03: degrau físico aberto 1 -> 2 (8 s) -> 1 (8 s).
Uso: python rc03_degrau.py DIRETORIO_NOVO
Requer acesso local ao Automation Studio para retorno se comunicação falhar.
"""
import asyncio
import csv
import json
import math
import sys
import time
from pathlib import Path
from asyncua import Client, ua

URL = "opc.tcp://10.0.0.2:4840"

async def sequence(write, record, restore):
    # finally cobre também escrita cujo resultado seja incerto.
    try:
        await write(2.0)
        await record("degrau", 8.0, 2.0)
    finally:
        await restore()
    await record("retorno", 8.0, 1.0)

async def run(out, report):
    async with Client(URL, timeout=5) as client:
        namespaces = await client.get_namespace_array()
        ns = namespaces.index("urn:B&R/pv/")
        nodes = [client.get_node(ua.NodeId("::Program:" + n, ns))
                 for n in ("ACAO_CONTROLE", "ADC_R")]
        for node in nodes:
            if await node.read_data_type_as_variant_type() != ua.VariantType.Float:
                raise RuntimeError("Exige REAL/Float em ambas as variaveis.")

        async def read():
            values = await client.read_values(nodes)
            if not all(isinstance(v, (float, int)) and math.isfinite(v)
                       for v in values):
                raise RuntimeError("Leitura invalida: " + repr(values))
            return values

        async def write(value):
            report["escritas_solicitadas"].append({
                "valor": value, "tempo_pc_s": time.monotonic() - start
            })
            await nodes[0].write_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(ua.Variant(value, ua.VariantType.Float))
            )

        initial, pv = await read()
        report["comando_inicial"] = initial
        report["adc_inicial"] = pv
        if abs(initial - 1.0) > 1e-5:
            raise RuntimeError(
                f"ACAO_CONTROLE={initial}; esperado 1.0. Nenhuma escrita."
            )
        start = time.monotonic()
        print("Conectado ao RC. Baseline 2 s; degrau 2.0 por 8 s; retorno 1.0 por 8 s.")
        print("Fase        Tempo(s)     Comando       ADC_R", flush=True)
        with (out / "amostras.csv").open("x", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["fase", "tempo_pc_s", "tempo_fase_s",
                             "acao_controle_lida", "adc_r"])

            async def record(phase, duration, expected):
                begin = time.monotonic()
                deadline = begin + duration
                next_print = 0.0
                while time.monotonic() < deadline:
                    # Não prolongar o degrau esperando uma leitura bloqueada.
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    try:
                        u, y = await asyncio.wait_for(read(), timeout=remaining)
                    except asyncio.TimeoutError:
                        raise TimeoutError("Leitura nao concluiu na fase " + phase)
                    now = time.monotonic()
                    elapsed = now - begin
                    writer.writerow([phase, now - start, elapsed, u, y])
                    f.flush()
                    report["leituras"] += 1
                    if abs(u - expected) > 1e-5:
                        raise RuntimeError(f"Comando divergente em {phase}: {u}")
                    if elapsed >= next_print:
                        print(f"{phase:10s} {now-start:8.3f} {u:11.5f} {y:11.5f}",
                              flush=True)
                        next_print = elapsed + 0.5
                    await asyncio.sleep(min(0.1, max(0, deadline-time.monotonic())))

            async def restore():
                try:
                    await write(1.0)
                    u, _ = await read()
                    if abs(u - 1.0) > 1e-5:
                        raise RuntimeError(f"Retorno divergente: {u}")
                    report["retorno_confirmado"] = True
                    print("Retorno a 1.0 confirmado por leitura.", flush=True)
                except BaseException as exc:
                    report["erro_retorno"] = repr(exc)
                    print("RETORNO NAO CONFIRMADO: restaurar ACAO_CONTROLE=1.0 "
                          "no Automation Studio.", flush=True)
                    raise

            await record("inicial", 2.0, 1.0)
            await sequence(write, record, restore)
        report["resultado"] = "COLETA_CONCLUIDA"

def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    report = {"teste": "RC-03", "resultado": "INCOMPLETO", "endpoint": URL,
              "retorno_confirmado": False, "leituras": 0,
              "escritas_solicitadas": []}
    try:
        asyncio.run(run(out, report))
    except BaseException as exc:
        report["erro"] = repr(exc)
        raise
    finally:
        (out / "resumo.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("Resultado:", report["resultado"])
        print("Evidencias:", out)

if __name__ == "__main__":
    main()
