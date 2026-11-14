"""RC-04: PI fixo no FORTE; escrita fisica OPC UA. Kp=Ki=6, Kd=0."""
import asyncio, csv, datetime, hashlib, json, math, sys, time
from pathlib import Path

SOURCE = Path.home() / "Documents/ensaios-RC/observacao-20261113-174038-736"
sys.path.insert(0, str(SOURCE))
from observar import runtime, event, EXE, HASH
from forte_local import RES, FB

URL = "opc.tcp://10.0.0.2:4840"
TS = 0.2

async def main(out, report):
    from asyncua import Client, ua
    if hashlib.sha256(EXE.read_bytes()).hexdigest() != HASH:
        raise RuntimeError("FORTE diferente do checkpoint.")
    report["sha256_exe"] = HASH
    with runtime(out) as m:
        for pin in ("PROPORTIONAL_TERM", "INTEGRAL_TERM", "SATURATED"):
            m.call(RES, "CREATE", "Watch", Source=FB+"."+pin, Destination="*")
        settings = dict(PROPORTIONAL_GAIN=6, INTEGRAL_GAIN=6, DERIVATIVE_GAIN=0,
                        SAMPLING_TIME_S=TS, OUTPUT_MIN=0, OUTPUT_MAX=2,
                        MANUAL="TRUE", MANUAL_OUTPUT=1, RESET="FALSE")
        for n, v in settings.items():
            m.write(n, v)
        event(m, "INIT", "INITO")
        async with Client(URL, timeout=2) as cl:
            ns = (await cl.get_namespace_array()).index("urn:B&R/pv/")
            nodes = [cl.get_node(ua.NodeId("::Program:"+n, ns))
                     for n in ("ACAO_CONTROLE", "ADC_R")]
            for n in nodes:
                if await n.read_data_type_as_variant_type() != ua.VariantType.Float:
                    raise RuntimeError("Exige REAL/Float.")
            async def read():
                u, y = await cl.read_values(nodes)
                if not all(isinstance(x, (int,float)) and math.isfinite(x)
                           for x in (u,y)):
                    raise RuntimeError("Leitura nao finita.")
                if not -0.1 <= y <= 2.2:
                    raise RuntimeError("ADC_R fora da faixa do ensaio: "+str(y))
                return u, y
            async def write(v):
                if not math.isfinite(v) or not 0 <= v <= 2:
                    raise RuntimeError("Comando fora de 0..2.")
                report["escritas_solicitadas"] += 1
                await nodes[0].write_attribute(
                    ua.AttributeIds.Value, ua.DataValue(ua.Variant(float(v),ua.VariantType.Float)))
            initial, y = await read()
            report["comando_inicial"] = initial
            if min(abs(initial),abs(initial-1)) > 1e-5:
                raise RuntimeError("Inicio exige comando 0 ou 1.")
            with (out/"amostras.csv").open("x",newline="",encoding="utf-8") as f:
                w=csv.writer(f)
                w.writerow(["fase","k","tempo_pc_s","dt_pc_s","sp","adc_r",
                            "acao_lida","acao_solicitada","erro_forte","p","i","saturado"])
                start=time.monotonic()
                last=1.0
                try:
                    await write(1.0)
                    print("Preparando comando 1.0 por 8 s...",flush=True)
                    end=time.monotonic()+8
                    while time.monotonic()<end:
                        u,y=await read()
                        if abs(u-1)>1e-5: raise RuntimeError("Comando inicial sobrescrito.")
                        w.writerow(["preparo","",time.monotonic()-start,"","",y,u,1,"","","",""])
                        f.flush()
                        await asyncio.sleep(.2)
                    if abs(y-1)>.08:
                        raise RuntimeError("Resposta nao estabilizou perto de 1.")
                    m.write("SETPOINT",1);m.write("PROCESS_VARIABLE",format(y,".17g"))
                    event(m,"REQ","CNF")  # estabelece saida manual 1
                    m.write("MANUAL","FALSE")
                    base=time.monotonic();previous=None
                    print("PI FORTE: Kp=6 Ki=6 Kd=0 Ts=0.2; saida 0..2")
                    print("k | SP | ADC_R | comando | P | I",flush=True)
                    for k in range(120):
                        await asyncio.sleep(max(0,base+k*TS-time.monotonic()))
                        u,y=await read();now=time.monotonic()
                        dt=None if previous is None else now-previous
                        if dt is not None and not .15<=dt<=.25:
                            raise RuntimeError("Intervalo PC fora de 200ms +/-50ms: "+str(dt))
                        previous=now
                        if abs(u-last)>1e-4:
                            raise RuntimeError("Comando lido diverge do ultimo enviado.")
                        sp=1.25 if 20<=k<70 else 1.0
                        m.write("SETPOINT",sp);m.write("PROCESS_VARIABLE",format(y,".17g"))
                        v=event(m,"REQ","CNF")
                        if v["CONFIGURATION_VALID"].upper() not in ("TRUE","1"):
                            raise RuntimeError("Configuracao invalida no FORTE.")
                        cmd=float(v["OUTPUT"])
                        if abs(float(v["ERROR"])-(sp-y))>1e-5:
                            raise RuntimeError("Erro do FORTE divergente.")
                        if time.monotonic()-now>TS:
                            raise TimeoutError("Calculo/transporte FORTE excedeu 200ms.")
                        await write(cmd);last=cmd
                        w.writerow(["PI",k+1,now-start,dt,sp,y,u,cmd,
                                    v["ERROR"],v["PROPORTIONAL_TERM"],
                                    v["INTEGRAL_TERM"],v["SATURATED"]]);f.flush()
                        report["amostras_pi"]=k+1
                        if k%5==0 or k in (19,20,69,70,119):
                            print(f'{k+1:3} | {sp:.2f} | {y:.5f} | {cmd:.5f} | '
                                  f'{float(v["PROPORTIONAL_TERM"]):.5f} | '
                                  f'{float(v["INTEGRAL_TERM"]):.5f}',flush=True)
                finally:
                    try:
                        await write(1.0)
                        u,y=await read()
                        if abs(u-1)>1e-5: raise RuntimeError("Retorno divergente.")
                        report["retorno_confirmado"]=True
                        print("ACAO_CONTROLE=1.0 confirmado.",flush=True)
                    except BaseException as exc:
                        report["erro_retorno"]=repr(exc)
                        print("RETORNO NAO CONFIRMADO: restaurar 1.0 no Automation Studio.",flush=True)
                        raise
                end=time.monotonic()+8
                while time.monotonic()<end:
                    u,y=await read()
                    if abs(u-1)>1e-5: raise RuntimeError("Comando alterado apos retorno.")
                    w.writerow(["retorno","",time.monotonic()-start,"","",y,u,1,"","","",""])
                    f.flush();await asyncio.sleep(.2)
    report["resultado"]="COLETA_CONCLUIDA"

def entry():
    out=Path.home()/"Documents/ensaios-RC"/("pi66-"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    out.mkdir(parents=True)
    r=dict(teste="RC-04",resultado="INCOMPLETO",kp=6,ki=6,kd=0,ts_s=TS,
           limites_saida=[0,2],amostras_pi=0,escritas_solicitadas=0,retorno_confirmado=False)
    (out/"script_executado.py").write_bytes(Path(__file__).read_bytes())
    for name in ("observar.py","forte_local.py"):
        (out/name).write_bytes((SOURCE/name).read_bytes())
    try:
        asyncio.run(main(out,r))
    except BaseException as exc:
        r["erro"]=repr(exc)
        raise
    finally:
        (out/"resumo.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
        print("RC-04:",r["resultado"],"| Evidencias:",out)
if __name__=="__main__":entry()
