#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mesma ideia do cadastrar_medicoes_saida_horizontal.py, mas pra Chegada.

🔶 REVERTE A MESMA DECISÃO registrada em cadastrar_checklist_horizontal.py
("campo de medição já é papel do Folhão"): os 6 "resumos" de Chegada
(RESUMOS_CHEGADA + RESUMOS_CHEGADA_INCERTOS) nasceram como sim_nao, mas
no Folhão são tabelas de medição de verdade (Gap, Cangalhas, Pass Line,
Cilindros, Rolos, Graxa) — 341 campos ao todo.

Roda isso NO SEU computador (a rede da sessão do Claude bloqueia a API
de produção por política). Requer só Python 3 (usa urllib) + o arquivo
mapeamentos_chegada.json na MESMA pasta.

USO:
    python cadastrar_medicoes_chegada_horizontal.py
"""
import json
import os
import urllib.request

API_BASE = "https://api-oms-csn.onrender.com"
OPERADOR = "CBK3574"  # confirmado pelo usuário como a própria matrícula

PASTA = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PASTA, "mapeamentos_chegada.json"), encoding="utf-8") as f:
    MAPEAMENTOS = json.load(f)


def chamar(path, payload=None, metodo="GET"):
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=metodo,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("Buscando etapas de 'horizontal-mcc4'...")
    etapas = chamar("/api/checklist-execucao/etapas/horizontal-mcc4")
    etapas_chegada = [e for e in etapas if e.get("area") == "chegada"]
    print(f"Achei {len(etapas_chegada)} etapa(s) na área Chegada.")

    for texto, mapa in MAPEAMENTOS.items():
        etapa = next((e for e in etapas_chegada if e["texto"].strip() == texto.strip()), None)
        if not etapa:
            print(f"⚠️  NÃO achei uma etapa com o texto exato: {texto!r}")
            print("    Confira se o texto cadastrado bate certinho (acentos, travessão —, vírgulas, etc.)")
            continue

        payload = {
            "id": etapa["id"],
            "texto": etapa["texto"],
            "operador": OPERADOR,
            "tipo_resposta": "medicao_multipla",
            "folhao_campo": json.dumps(mapa, ensure_ascii=False),
        }
        resultado = chamar("/api/checklist-execucao/etapas/editar", payload, metodo="POST")
        print(f"✅ Etapa #{etapa['id']} ({texto[:50]}...) -> {resultado} ({len(mapa)} campos)")

    print("\nPronto. Recarrega o Checklist de Execução do Horizontal e confere.")


if __name__ == "__main__":
    main()
